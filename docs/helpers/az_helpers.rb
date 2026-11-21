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
end
