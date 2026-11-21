require 'json'

# The Components and Patterns indexes share one template (partials/_az_index)
# and one pagination model. Entries are split into one page per letter, A to Z,
# followed by a single 0-9 page. Only buckets that hold entries get a page; the
# first of those is the section index itself, so no page is published twice.
module AzHelpers
  AZ_BUCKETS = (('A'..'Z').to_a + ['0-9']).freeze
  AZ_SECTIONS = {
    'components' => { 'title' => 'Components', 'path' => '/components/index.html' },
    'patterns' => { 'title' => 'Patterns', 'path' => '/patterns/index.html' }
  }.freeze

  # The bucket is the first letter or digit read left to right, so a title that
  # opens with a quotation mark, bracket or symbol sorts under what follows it.
  # Accents are ignored: "Écran" belongs under E.
  def az_bucket_for(title)
    first = title.to_s.unicode_normalize(:nfd).gsub(/\p{Mn}/, '')[/[A-Za-z0-9]/]
    return nil if first.nil?

    first.match?(/\d/) ? '0-9' : first.upcase
  end

  # Sorts within a bucket by the title with any leading symbols removed.
  def az_sort_key(title)
    title.to_s.unicode_normalize(:nfd).gsub(/\p{Mn}/, '').sub(/\A[^A-Za-z0-9]+/, '').downcase
  end

  def az_slug(bucket)
    bucket.downcase
  end

  # Each entry: title, href (nil when there is no page yet), summary, meta, id.
  def az_entries(section)
    entries = case section
              when 'components'
                component_parents.map do |parent|
                  { 'title' => parent.fetch('parent'), 'href' => parent.fetch('available') ? parent.fetch('route') : nil,
                    'summary' => nil, 'id' => parent.fetch('list_anchor'),
                    'meta' => component_origin_summary(parent) + (parent.fetch('available') ? '' : ' · Specification not yet published') }
                end
              when 'patterns'
                section_groups('patterns').flat_map(&:last).uniq.map do |resource|
                  { 'title' => resource.data.title, 'href' => '/' + resource.destination_path,
                    'summary' => resource.data.description, 'id' => 'entry-' + component_slug(resource.data.title),
                    'meta' => resource.data.status == 'reference' ? 'Reference pattern · adapt and test before connecting to Home Assistant' : nil }
                end
              else
                raise "Unknown A to Z section: #{section}"
              end
    entries.each { |entry| entry['bucket'] = az_bucket_for(entry.fetch('title')) }
    unplaced = entries.select { |entry| entry['bucket'].nil? }
    raise "No letter or number in: #{unplaced.map { |entry| entry['title'] }.join(', ')}" unless unplaced.empty?

    entries.sort_by { |entry| [az_sort_key(entry.fetch('title')), entry.fetch('title')] }
  end

  def az_buckets(section)
    @az_buckets ||= {}
    @az_buckets[section] ||= az_entries(section).group_by { |entry| entry.fetch('bucket') }
                                                .sort_by { |bucket, _| AZ_BUCKETS.index(bucket) }.to_h
  end

  def az_populated(section)
    az_buckets(section).keys
  end

  # The first populated bucket lives at the section index.
  def az_path(section, bucket)
    return AZ_SECTIONS.fetch(section).fetch('path') if bucket == az_populated(section).first

    "/#{section}/a-z/#{az_slug(bucket)}.html"
  end

  # Browser title: a letter page names its letter, for example "Components: B".
  def az_page_title
    bucket = current_page.metadata.fetch(:locals, {})[:az_bucket]
    bucket ? "#{current_page.data.title}: #{bucket}" : current_page.data.title
  end

  # True on every paged page except the section index itself.
  def az_letter_page?
    !current_page.metadata.fetch(:locals, {})[:az_bucket].nil?
  end

  def az_current_bucket(section)
    current_page.metadata.fetch(:locals, {})[:az_bucket] || az_populated(section).first
  end

  # Pages published for a section other than its index, for the proxies.
  def az_extra_pages(section)
    az_populated(section).drop(1).map { |bucket| [az_path(section, bucket), bucket] }
  end

  # First, previous, current, next and last, each with a target bucket or nil
  # when there is nowhere to go.
  def az_pager(section, bucket)
    populated = az_populated(section)
    position = populated.index(bucket)
    {
      first: position.positive? ? populated.first : nil,
      previous: position.positive? ? populated[position - 1] : nil,
      current: bucket,
      next: position < populated.length - 1 ? populated[position + 1] : nil,
      last: position < populated.length - 1 ? populated.last : nil
    }
  end

  # Anchor ids in the search data point at the page that holds the entry.
  def az_entry_path(section, entry)
    az_path(section, entry.fetch('bucket'))
  end

  # The page a letter page belongs to: itself for an index, otherwise the index
  # it is a letter of.
  def page_home_path
    current_page.metadata.fetch(:locals, {})[:az_home] || current_page.destination_path
  end

  # Lexicons (A to Z General and A to Z Technical) keep one authored source
  # each. Their rendered letter sections are split into one page per letter at
  # build time, so every entry anchor is unchanged and only its page differs.
  # The registry holds, for each lexicon, its populated letters and the letter
  # that holds each anchor.
  def az_lexicon_registry(html)
    segments = html.split(/(?=<h2 class="style-a-z__letter" id=")/).drop(1)
    populated = []
    anchors = {}
    segments.each do |segment|
      bucket = segment[/id="([a-z0-9-]+)"/, 1].upcase
      bucket = '0-9' if bucket =~ /\A\d/
      populated << bucket
      segment.scan(/\bid="([^"]+)"/).flatten.each { |anchor| anchors[anchor] = bucket }
    end
    { populated: AZ_BUCKETS & populated, anchors: anchors }
  end

  def az_lexicon_page_for(home, bucket, populated)
    bucket == populated.first ? home : home.sub(/\.html\z/, "-#{az_slug(bucket)}.html")
  end

  def az_lexicon_page?
    !!current_page.data.az_lexicon
  end

  # Keeps the current letter's entries and puts the shared bar and pager around
  # them. The introduction is shown on the first page only.
  def az_lexicon_apply(fragment)
    home = page_home_path
    lexicon = config[:az_lexicons].fetch(home)
    populated = lexicon[:populated]
    bucket = current_page.metadata.fetch(:locals, {})[:az_bucket] || populated.first
    hrefs = populated.to_h { |letter| [letter, docs_path('/' + az_lexicon_page_for(home, letter, populated))] }
    fragment.at_css('nav[aria-label="A to Z navigation"]')&.unlink
    intro = []
    sections = Hash.new { |hash, key| hash[key] = [] }
    current = nil
    fragment.children.to_a.each do |node|
      if node.name == 'h2' && node['class'].to_s.include?('style-a-z__letter')
        current = node['id'].upcase
        current = '0-9' if current =~ /\A\d/
      end
      (current ? sections[current] : intro) << node.unlink
    end
    heading = intro.find { |node| node.name == 'h1' }
    kept = bucket == populated.first ? intro : [heading].compact
    kept.each { |node| fragment.add_child(node) }
    fragment.add_child(partial('partials/az_bar', locals: { bucket: bucket, hrefs: hrefs }))
    sections[bucket].each { |node| fragment.add_child(node) }
    fragment.add_child(partial('partials/az_pager', locals: { bucket: bucket, hrefs: hrefs, label: current_page.data.title }))
  end

  # A link to an entry in a lexicon points at the letter page that holds it.
  def az_rewrite_lexicon_links(fragment)
    lexicons = config[:az_lexicons]
    folder = File.dirname('/' + current_page.destination_path)
    current_lexicon = lexicons[page_home_path]
    current_bucket = current_page.metadata.fetch(:locals, {})[:az_bucket] || current_lexicon&.fetch(:populated)&.first
    fragment.css('a[href^="#"]').each do |link|
      anchor = link['href'][1..]
      bucket = current_lexicon && current_lexicon[:anchors][anchor]
      next if bucket.nil? || bucket == current_bucket

      link['href'] = docs_path('/' + az_lexicon_page_for(page_home_path, bucket, current_lexicon[:populated])) + '#' + anchor
    end
    fragment.css('a[href*="a-to-z.html#"]').each do |link|
      uri = URI.parse(link['href']) rescue next
      next if uri.host || uri.path.to_s.empty? || uri.fragment.to_s.empty?

      target = Pathname.new(File.join(folder, uri.path)).cleanpath.to_s.sub(%r{\A/}, '')
      lexicon = lexicons[target]
      bucket = lexicon && lexicon[:anchors][uri.fragment]
      next if bucket.nil? || bucket == lexicon[:populated].first

      link['href'] = docs_path('/' + az_lexicon_page_for(target, bucket, lexicon[:populated])) + '#' + uri.fragment
    end
  end
end
