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

  def component_slug(text)
    text.downcase.gsub('&', 'and').gsub(/[^a-z0-9]+/, '-').gsub(/\A-|-\z/, '')
  end

  def component_letter_groups
    component_parents.group_by { |parent| parent.fetch('letter') }
  end

  def component_origin_summary(parent)
    parent.fetch('origins').join(', ')
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
  def component_search_json
    JSON.generate(component_index_entries.map do |entry|
      href = if entry.fetch('available')
               docs_path(entry.fetch('route')) + (entry['anchor'] && entry['anchor_published'] ? '#' + entry['anchor'] : '')
             else
               '#parent-' + component_slug(entry.fetch('owner'))
             end
      { 'n' => entry.fetch('name'), 'k' => entry.fetch('kind'), 'o' => entry.fetch('owner'), 'h' => href,
        'a' => entry.fetch('available'), 'w' => entry['within'] }.compact
    end).gsub('</', '<\/')
  end
end
