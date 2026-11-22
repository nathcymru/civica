module DesignSystemHelpers
  SECTION_GROUP_ORDER = ['Guidance', 'Colour', 'Typography', 'Structure', 'Icons and images', 'Data visualisation', 'Illustration', 'Writing standards', 'Writing guidelines', 'Formatting content', 'Publish, update or retire', 'Lexicons', 'Quick reference', 'Home Assistant components', 'Form elements', 'Content presentation', 'Navigation', 'Publishing components', 'Task patterns', 'Page patterns', 'Inclusive content', 'Publishing patterns', 'Publishing guide', 'Home Assistant: controls', 'Home Assistant: flows', 'Home Assistant: interface coverage', 'Page templates', 'Review'].freeze
  def escape(value)
    ERB::Util.html_escape(value.to_s)
  end

  def repository_licence_markdown
    # One authored Markdown source; only repo-relative notice links are resolved
    # to their copied public files for the static documentation site.
    File.read(File.expand_path('../LICENSE.md', root)).gsub(/\]\((licences\/[^)]+)\)/) do
      "](#{docs_path('/reference/' + Regexp.last_match(1))})"
    end.gsub(/\]\(docs\/source(\/images\/[^)]+)\)/) do
      "](#{docs_path(Regexp.last_match(1))})"
    end
  end

  # The deployed notice and its catalogue example use one markup record.
  # Only destinations and persistence mode differ in the live documentation shell.
  def site_notice
    fragment = Nokogiri::HTML::DocumentFragment.parse(config[:civica_examples].fetch('core-cookie-essential').fetch('html'))
    notice = fragment.at_css('[data-site-notice]')
    notice['data-site-notice'] = 'live'
    notice['data-docs-home'] = docs_path('/index.html')
    fragment.at_css('[data-site-cookies]')['href'] = docs_path('/community/cookies.html')
    fragment.to_html
  end

  # A paged index page (one letter of Components or Patterns) shows the same
  # section artwork as the section index it belongs to.
  def page_illustration
    data['page-illustrations'][page_home_path]
  end

  def home_page?
    current_page.destination_path == 'index.html'
  end

  def guide_pages
    sitemap.resources.select do |resource|
      resource.destination_path.end_with?('.html') && resource.data.title && !config[:az_letter_pages].include?(resource.destination_path) &&
        !resource.destination_path.start_with?('examples/') && !resource.ignored?
    end
  end

  def section_for(resource)
    resource.data.section || resource.destination_path.split('/').first
  end

  def section_groups(section)
    section_home = data.navigation.sections.find { |item| item.id == section }&.path
    pages = guide_pages.select do |resource|
      section_for(resource) == section && '/' + resource.destination_path != section_home &&
        resource.data.status != 'retired' &&
        (!resource.destination_path.end_with?('/index.html') || resource.destination_path == 'home-assistant/index.html')
    end
    pages.group_by { |resource| resource.data.group || (section == 'components' ? 'Home Assistant components' : 'Guidance') }
      .sort_by { |group, _| ['Guidance', 'Colour', 'Typography', 'Structure', 'Icons and images', 'Data visualisation', 'Illustration', 'Writing guidelines', 'Formatting content', 'Publish, update or retire', 'Lexicons', 'Writing standards', 'Quick reference', 'Home Assistant components', 'Home Assistant: controls', 'Home Assistant: flows', 'Form elements', 'Content presentation', 'Navigation', 'Inclusive content', 'Task patterns', 'Page patterns', 'Publishing components', 'Publishing patterns', 'Page templates'].index(group) || 99 }
      .map { |group, resources| [group, resources.sort_by { |resource| [resource.data.nav_order || 100, resource.data.title.downcase] }] }
  end

  # The section menu used on every section: "Introduction" first, then one
  # top-level item per group. A group with an overview page links to it and lists
  # its other pages below; a group with one page is a plain link; a group with
  # several pages and no overview page links to its first page and lists them all. Only the
  # branch the reader is in is open.
  def section_tree(section_id)
    section = data.navigation.sections.find { |item| item.id == section_id }
    home = guide_pages.find { |resource| '/' + resource.destination_path == section.path }
    tree = [{ title: 'Introduction', resource: home, children: [] }]
    pages = guide_pages.select do |resource|
      section_for(resource) == section_id && '/' + resource.destination_path != section.path && resource.data.status != 'retired'
    end
    default_group = section_id == 'components' ? 'Home Assistant components' : 'Guidance'
    groups = pages.group_by { |resource| resource.data.group || default_group }
    groups.sort_by { |group, _| [SECTION_GROUP_ORDER.index(group) || 99, group] }.each do |group, resources|
      sorted = resources.sort_by { |resource| [resource.data.nav_order || 100, resource.data.title.downcase] }
      overview = sorted.find { |resource| resource.data.nav_order == 0 } ||
                 sorted.find { |resource| resource.destination_path.end_with?('index.html') }
      if sorted.size == 1
        tree << { title: sorted.first.data.title, resource: sorted.first, children: [] }
      elsif overview
        tree << { title: overview.data.title, resource: overview, children: sorted - [overview] }
      else
        # No overview page: the group name links to its first page and every page
        # is listed below it, so there is never a toggle that behaves differently.
        tree << { title: group, resource: sorted.first, children: sorted, group_link: true }
      end
    end
    tree
  end

  # Search includes section hubs, which are intentionally absent from their own
  # sidebar. Keep this collection independent of the navigation filter.
  def search_groups
    guide_pages.reject { |resource| ['search.html', 'sitemap.html'].include?(resource.destination_path) }
      .group_by { |resource| resource.destination_path == 'index.html' ? 'Start here' : (data.navigation.sections.find { |item| item.id == section_for(resource) }&.title || 'Guidance') }
      .map { |group, resources| [group, resources.sort_by { |resource| resource.data.title.downcase }] }
  end

  def example(id)
    spec = config[:civica_examples].fetch(id) { raise "Unknown example #{id}" }
    partial 'partials/example', locals: { id: id, spec: spec }
  end

  # Resolve catalogue assets before escaping code examples. Middleman's normal
  # URL rewriter handles rendered tags, but cannot rewrite escaped code panels.
  # Both outputs use URLs relative to the standalone /examples/ document.
  def example_html(spec)
    html = spec.fetch('html')
    return html unless html.match?(/\.(?:css|js)(?:[?"'#]|\s)/)

    fragment = Nokogiri::HTML::DocumentFragment.parse(html)
    fragment.css('script[src], link[rel="stylesheet"][href]').each do |node|
      attribute = node.name == 'script' ? 'src' : 'href'
      uri = Addressable::URI.parse(node[attribute])
      next unless uri.scheme.nil? && uri.host.nil?
      next unless %w(.css .js).include?(File.extname(uri.path))

      source_path = Pathname.new('/examples').join(uri.path).cleanpath.to_s
      resource = sitemap.find_resource_by_path(source_path)
      next unless resource

      uri.path = Pathname.new('/' + resource.destination_path)
        .relative_path_from(Pathname.new('/examples')).to_s
      node[attribute] = uri.to_s
    end
    fragment.to_html
  end

  def component_family
    @civica_family_record ||= JSON.parse(File.read(File.join(root, 'data', 'component-rationalisation.json')))
    route = '/' + current_page.destination_path
    page = @civica_family_record['pageInventory'].find { |item| item['url'] == route }
    return nil unless page
    family = @civica_family_record['families'].find { |item| item['id'] == page['familyId'] }
    return nil unless family && family['memberPages'].length > 1
    { page: page, family: family, pages: @civica_family_record['pageInventory'] }
  end

  def page_history
    stored = data.respond_to?(:page_history) ? data.page_history[current_page.destination_path] : nil
    changes = current_page.data.updates || (stored && stored['updates'])
    raise "Missing page history: #{current_page.destination_path}" unless changes && !changes.empty?
    {
      published: current_page.data.published_on || stored['published_on'],
      updated: current_page.data.updated_on || stored['updated_on'],
      changes: changes.each_with_index.sort_by { |change, index| [-Date.parse(change['date'].to_s).jd, index] }.map(&:first)
    }
  end

  def readable_date(value)
    Date.parse(value.to_s).strftime('%-d %B %Y')
  end
end
