require 'json'

# The Components index, its A to Z jump bar, the combobox search data, the
# sidebar and /reference/component-index.json all come from one record:
# docs/data/component-inventory.json. Nothing here keeps a second list.
module ComponentHelpers
  COMPONENT_LETTERS = ('A'..'Z').to_a.freeze

  def component_inventory
    @component_inventory ||= JSON.parse(File.read(File.join(root, 'data', 'component-inventory.json')))
  end

  def component_resource(route)
    path = route.sub(%r{\A/}, '')
    sitemap.resources.find { |resource| resource.destination_path == path && !resource.ignored? }
  end

  # A parent is published only when its page exists in the build. Pending
  # parents are listed honestly and never linked.
  def component_parents
    @component_parents ||= component_inventory.fetch('parents').map do |parent|
      resource = component_resource(parent.fetch('route'))
      parent.merge('available' => !resource.nil?, 'resource' => resource,
                   'declared' => !resource.nil? && !resource.data.component.nil?,
                   'list_anchor' => 'parent-' + component_slug(parent.fetch('parent')))
    end
  end

  # Pages in /components/ that are not inventory parents. They are kept in the
  # sidebar only until Branch 2 retires or moves them; the check pins this list
  # so it can shrink but never grow.
  def component_legacy_pages
    routes = component_inventory.fetch('parents').map { |parent| parent.fetch('route').sub(%r{\A/}, '') }
    sitemap.resources.select do |resource|
      path = resource.destination_path
      path.start_with?('components/') && path.end_with?('.html') && path != 'components/index.html' &&
        !resource.ignored? && !config[:az_letter_pages].include?(resource.destination_path) && !routes.include?(path)
    end
  end

  # The sidebar: every published parent, plus the legacy pages above, in one
  # flat list in the inventory's order (lower-case code points).
  def component_sidebar_items
    items = component_parents.select { |parent| parent.fetch('available') }
                             .map { |parent| { 'name' => parent.fetch('parent'), 'resource' => parent.fetch('resource') } } +
            component_legacy_pages.map { |resource| { 'name' => resource.data.title.to_s, 'resource' => resource } }
    items.sort_by { |item| item.fetch('name').downcase }
  end

  def component_slug(text)
    text.downcase.gsub('&', 'and').gsub(/[^a-z0-9]+/, '-').gsub(/\A-|-\z/, '')
  end

  def component_letter_groups
    component_parents.group_by { |parent| parent.fetch('letter') }
  end

  # One entry for each parent, child and grandchild, in inventory order.
  # A cross-referenced element points at its single owner anchor.
  def component_index_entries
    component_parents.flat_map do |parent|
      own = { 'name' => parent.fetch('parent'), 'kind' => 'parent', 'owner' => parent.fetch('parent'),
              'route' => parent.fetch('route'), 'anchor' => nil, 'available' => parent.fetch('available'),
              'anchor_published' => parent.fetch('declared') }
      [own] + parent.fetch('children').flat_map do |child|
        [component_entry(parent, child, 'child')] +
          child.fetch('grandchildren', []).map { |item| component_entry(parent, item, 'grandchild', child.fetch('name')) }
      end
    end
  end

  def component_entry(parent, item, kind, within = nil)
    target = item['cross_reference']
    owner = target ? component_parents.find { |candidate| candidate.fetch('parent') == target.fetch('parent') } : parent
    entry = { 'name' => item.fetch('name'), 'kind' => kind, 'origin' => item['origin'],
              'owner' => owner.fetch('parent'), 'route' => owner.fetch('route'),
              'anchor' => target ? target.fetch('anchor') : item.fetch('anchor'),
              'available' => owner.fetch('available'),
              'anchor_published' => owner.fetch('declared') }
    entry['within'] = within if within
    entry['listed_on'] = parent.fetch('parent') if target
    entry['note'] = item['note'] if item['note']
    entry
  end

  # Front matter `component:` blocks are reported so the schema check can prove
  # each page declares exactly what the inventory assigns to it.
  def component_declarations
    component_parents.select { |parent| parent.fetch('available') }.map do |parent|
      { 'route' => parent.fetch('route'), 'declared' => parent.fetch('resource').data.component.to_h }
    end
  end

  def component_index_document
    {
      'schema_version' => 1,
      'source' => 'docs/data/component-inventory.json',
      'locked_on' => component_inventory.fetch('locked_on'),
      'rules' => component_inventory.fetch('rules'),
      'counts' => {
        'parents' => component_parents.length,
        'published_parents' => component_parents.count { |parent| parent.fetch('available') },
        'parents_with_declared_schema' => component_parents.count { |parent| parent.fetch('declared') }
      },
      'parents' => component_parents.map do |parent|
        { 'name' => parent.fetch('parent'), 'route' => parent.fetch('route'), 'letter' => parent.fetch('letter'),
          'origins' => parent.fetch('origins'), 'available' => parent.fetch('available'), 'declared' => parent.fetch('declared'),
          'children' => parent.fetch('children') }
      end,
      'entries' => component_index_entries,
      'declarations' => component_declarations
    }
  end

  # The browser copy drops the bulky parent records; it needs only the entries.
  # A cross-referenced element resolves to the same anchor as its owner entry,
  # so it is folded into that entry ("also listed on") instead of repeating it.
  def component_search_json
    entries = component_index_entries
    also = Hash.new { |hash, key| hash[key] = [] }
    entries.each { |entry| also[[entry.fetch('name'), entry.fetch('owner')]] << entry if entry['listed_on'] }
    JSON.generate(entries.reject { |entry| entry['listed_on'] }.map do |entry|
      href = if entry.fetch('available')
               docs_path(entry.fetch('route')) + (entry['anchor'] && entry['anchor_published'] ? '#' + entry['anchor'] : '')
             else
               docs_path(az_path('components', az_bucket_for(entry.fetch('owner')))) + '#parent-' + component_slug(entry.fetch('owner'))
             end
      listed = also[[entry.fetch('name'), entry.fetch('owner')]]
      # Only cross-reference notes are shown; other inventory notes are internal records.
      notes = listed.map { |item| item['note'] }.compact
      { 'n' => entry.fetch('name'), 'k' => entry.fetch('kind'), 'o' => entry.fetch('owner'), 'h' => href,
        'a' => entry.fetch('available'), 'w' => entry['within'],
        'g' => entry['origin'] && component_origin_label(entry['origin']),
        'l' => listed.empty? ? nil : listed.map { |item| item.fetch('listed_on') },
        't' => notes.empty? ? nil : notes.join(' ') }.compact
    end).gsub('</', '<\/')
  end

  # Display form of an origin. The data value is "Civica"; the brand is written Civica.
  def component_origin_label(origin)
    origin == 'Civica' ? 'Civica' : origin
  end

  def component_origin_summary(parent)
    'Origin: ' + parent.fetch('origins').map { |origin| component_origin_label(origin) }.join(', ')
  end
end
