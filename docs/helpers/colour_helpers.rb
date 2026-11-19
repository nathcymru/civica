require 'json'
require 'yaml'
require 'digest'
require 'nokogiri'

# The Colour section renders every swatch from one record:
# docs/data/govuk-brand-colours.json, copied verbatim from the GOV.UK Brand
# Guidelines colour pages. Pages never type a colour value themselves.
module ColourHelpers
  def govuk_colours
    @govuk_colours ||= JSON.parse(File.read(File.join(root, 'data', 'govuk-brand-colours.json')))
  end

  def govuk_colour(id)
    govuk_colours.fetch('colours').fetch(id) { raise "Unknown GOV.UK colour #{id}" }
  end

  # Section hero colours: the darkest step that gives white text 4.5:1, and a
  # pale tint for the art panel. Mirrors docs/scripts/generate-hero-art.py.
  def hero_colours(family)
    dark = %w[shade-25 shade-50].map { |step| govuk_colours.fetch('colours')["#{family}-#{step}"] }.compact.find do |colour|
      channels = colour['rgb'].map { |value| value / 255.0 }.map { |c| c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055)**2.4 }
      1.05 / (0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2] + 0.05) >= 4.5
    end
    raise "No hero colour for #{family}" unless dark
    [dark['hex'], govuk_colour("#{family}-tint-95")['hex']]
  end

  def colour_slug(text)
    text.downcase.gsub('&', 'and').gsub(/[^a-z0-9]+/, '-').gsub(/\A-|-\z/, '')
  end

  def colour_page(page)
    govuk_colours.fetch('pages').fetch(page)
  end

  # WCAG 2.2 relative luminance and contrast ratio.
  def colour_luminance(hex)
    channels = hex.delete('#').scan(/../).map { |pair| pair.to_i(16) / 255.0 }
    linear = channels.map { |c| c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055)**2.4 }
    0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
  end

  def colour_contrast(first, second)
    a, b = [colour_luminance(first), colour_luminance(second)].sort.reverse
    (a + 0.05) / (b + 0.05)
  end

  # "Copy hex #1D70B8 for Primary blue": lower case mid-sentence, except initialisms and names.
  def colour_spoken_label(label)
    %w[RGB CMYK Pantone].include?(label) ? label : label.downcase
  end

  COPY_ICON = '<svg class="c-copy-value__icon" viewBox="0 0 18 18" width="18" height="18" aria-hidden="true" focusable="false">' \
              '<polygon points="12.58 16.51 2.27 16.51 2.27 3.35 3.27 3.35 3.27 15.51 12.58 15.51 12.58 16.51"/>' \
              '<path d="M15.73,13.91H4.88V1.49h10.86v12.42ZM5.88,12.91h8.86V2.49H5.88v10.42Z"/></svg>'.freeze

  # One value line, as GOV.UK shows it: "RGB 29 112 184" or "#1D70B8", then
  # an icon-only copy button. The value stays selectable text; the button is
  # shown by JavaScript only where the Clipboard API exists.
  # `key` keeps the id unique when one colour value appears in several swatches.
  def colour_value_row(label, value, colour_name, copy: true, key: nil, show_label: true)
    id = 'v-' + Digest::SHA1.hexdigest("#{key}|#{colour_name}|#{label}|#{value}")[0, 10]
    prefix = show_label ? %(<span class="c-swatch__label">#{escape(label)}</span> ) : ''
    button = copy ? %(<button type="button" class="c-copy-value" data-copy-value="#{escape(value)}" aria-label="Copy #{escape(colour_spoken_label(label))} #{escape(value)} for #{escape(colour_name)}" hidden>#{COPY_ICON}</button>) : ''
    %(<dd class="c-swatch__value">#{prefix}<code id="#{id}">#{escape(value)}</code>#{button}</dd>)
  end

  # One swatch in the GOV.UK Brand layout: a circular sample, the name in bold,
  # then each value with its copy button. Screen pages show RGB and hex; the
  # print page shows CMYK and Pantone, in the GOV.UK order.
  def colour_swatch(id, fields: %i[rgb hex], role: nil, name: nil, key: nil, note: nil)
    colour = govuk_colour(id)
    name ||= role ? "#{role}: #{colour.fetch('name')}" : colour.fetch('name')
    hex = colour.fetch('hex')
    rows = fields.filter_map do |field|
      case field
      when :rgb then colour_value_row('RGB', colour.fetch('rgb').join(' '), name, key: key)
      when :hex then colour_value_row('Hex', hex, name, key: key, show_label: false)
      when :cmyk then colour_value_row('CMYK', colour.dig('print', 'cmyk').join(' '), name, key: key) if colour['print']
      when :pantone then colour_value_row('Pantone', colour.dig('print', 'pantone'), name, key: key, show_label: false) if colour['print']
      end
    end
    rows << %(<dd class="c-swatch__value">No print value given</dd>) if fields.include?(:cmyk) && !colour['print']
    rows << %(<dd class="c-swatch__note">#{escape(note)}</dd>) if note
    %(<div class="c-swatch" style="--c-swatch-colour:#{hex};"><dt class="c-swatch__name">#{escape(name)}</dt>#{rows.join}</div>)
  end

  def colour_swatch_list(items, compact: false)
    %(<dl class="c-swatch-list#{' c-swatch-list--compact' if compact}">#{items.join}</dl>)
  end

  def colour_swatches(ids, compact: false, **options)
    colour_swatch_list(ids.map { |id| colour_swatch(id, **options) }, compact: compact)
  end

  # A palette as GOV.UK groups it: one heading and one swatch list per group.
  def colour_palette(page, level: 3, **options)
    colour_groups(colour_page(page).fetch('palette'), level: level, **options)
  end

  def colour_groups(groups, level: 3, **options)
    groups.map do |group|
      %(<h#{level} id="#{colour_slug(group.fetch('title'))}">#{escape(group.fetch('title'))}</h#{level}>\n) + colour_swatches(group.fetch('colours'), **options)
    end.join("\n")
  end

  # "The web palette has:" list of links to each group, as GOV.UK opens it.
  # The chart page lists its categorical, scale and additional groups.
  def colour_group_links(page, extra = {})
    groups = if page == 'charts'
               [['categorical colours', '#categorical-palette']] +
                 colour_page('charts').fetch('sequential').map { |group| [group.fetch('title').downcase, "##{colour_slug(group.fetch('title'))}"] } +
                 [['additional colours', '#additional-palette-for-illustrative-infographics']]
             else
               colour_page(page).fetch('palette').map { |group| [group.fetch('title').downcase, "##{colour_slug(group.fetch('title'))}"] }
             end
    links = groups + extra.to_a
    %(<ul>#{links.map { |text, href| %(<li><a href="#{href}">#{escape(text)}</a></li>) }.join}</ul>)
  end

  # Chart categorical colours, in the GOV.UK order, then the colours for axes
  # and lines and for labels, each under its own heading as GOV.UK shows them.
  def colour_chart_categorical(level: 4, **options)
    items = colour_page('charts').fetch('categorical')
    html = colour_swatch_list(items.reject { |item| item['role'] }.map { |item| colour_swatch(item.fetch('colour'), key: 'categorical', **options) })
    items.select { |item| item['role'] }.group_by { |item| item['role'] }.each do |role, group|
      html += %(\n<h#{level} id="#{colour_slug(role)}">#{escape(role)}</h#{level}>\n) + colour_swatch_list(group.map { |item| colour_swatch(item.fetch('colour'), key: 'categorical', **options) })
    end
    html
  end

  # GOV.UK social companion colour set: each pairing is named, shown as a
  # sample, and its two colours listed as swatches.
  def colour_companion_pairs(level: 4)
    colour_page('social').fetch('companion').each_with_index.map do |pair, index|
      fg = govuk_colour(pair.fetch('foreground'))
      bg = govuk_colour(pair.fetch('background'))
      label = "#{fg.fetch('name')} on #{bg.fetch('name')}"
      sample = %(<svg class="c-pair__sample" viewBox="0 0 320 320" aria-hidden="true" focusable="false"><rect width="320" height="320" fill="#{bg.fetch('hex')}"/><circle cx="160" cy="160" r="96" fill="#{fg.fetch('hex')}"/></svg>)
      swatches = colour_swatch_list([colour_swatch(pair.fetch('foreground'), key: "pair-#{index}"), colour_swatch(pair.fetch('background'), key: "pair-#{index}")])
      %(<h#{level} class="c-pair__name">#{escape(label)}</h#{level}>\n<div class="c-pair">#{sample}<div class="c-pair__colours">#{swatches}</div></div>)
    end.join("\n")
  end

  # Web functional colours: named by their GOV.UK token, as upstream shows them.
  def colour_functional_tokens(level: 3)
    colour_page('web').fetch('functional').map do |group|
      items = group.fetch('tokens').map { |token| colour_swatch(token.fetch('colour'), name: token.fetch('token')) }
      %(<h#{level} id="functional-#{colour_slug(group.fetch('title'))}">#{escape(group.fetch('title'))}</h#{level}>\n) + colour_swatch_list(items)
    end.join("\n")
  end

  def colour_id_by_name(name)
    @colour_ids_by_name ||= govuk_colours.fetch('colours').to_h { |id, colour| [colour.fetch('name'), id] }
    @colour_ids_by_name.fetch(name) { raise "Unknown GOV.UK colour name #{name}" }
  end

  # A colour example as GOV.UK shows it: the picture on the page, not in an
  # example frame. The pictures, the "invented data" labels and the data
  # tables come from the same example record as the standalone example page,
  # so there is one source. The record's own h2 is dropped, because the page
  # heading already names the example.
  #
  # layout:
  #   :figures  keep the record as it is (pictures with their captions)
  #   :tiles    each picture under its own heading, beside swatches for the
  #             colours its caption lists (GOV.UK tonal and companion examples)
  #   :chart    the chart, its notes and its data table (in a details
  #             element), with a compact swatch list for the colours it uses
  #   :map      the map, its key and its data table (in a details element)
  #   :scale    the social tone tiles in one row, without captions
  def colour_example(id, layout: :figures, callout: true, level: 4)
    spec = config[:civica_examples].fetch(id) { raise "Unknown example #{id}" }
    fragment = Nokogiri::HTML::DocumentFragment.parse(spec.fetch('html'))
    root = fragment.at_css('section') || fragment
    root.at_css('h2')&.remove
    lead = ''
    case layout
    when :tiles then lead = colour_example_tiles(root, id, level)
    when :chart then colour_example_chart(root, id)
    when :map
      # The page's "Colours used in example" section owns the colour list.
      root.css('> p').each { |para| para.remove if para.text.strip.start_with?('Colours used:') }
      colour_example_data_tables(root)
    when :scale
      # The inform-to-inspire scale: the 5 tiles in a row (wrapping on narrow screens) under the
      # axis. The page lists the options in order, so the record's own order
      # sentence and the per-tile captions are not repeated.
      root.css('figcaption').each(&:remove)
      root.css('figure').each { |figure| figure.remove_attribute('aria-labelledby') }
      root.css('> p').each { |para| para.content = 'The messages are invented examples.' if para.text.include?('In order:') }
      root.css('> div[style]').each { |grid| grid['style'] = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px' }
    end
    # Markdown wraps a line that starts with an inline-looking tag (such as
    # <figcaption>) in a paragraph, so emit the example as one line of HTML.
    html = (lead.empty? ? root.inner_html : lead).gsub(/^[ \t]+/, '').gsub(/\s*\n\s*/, ' ').strip
    html = html.sub('COLOUR-EXAMPLE-SWATCHES', @colour_example_swatches.to_s) if layout == :chart
    intro = lead.empty? ? '' : root.css('> p').map(&:to_html).join
    note = callout ? colour_callout : ''
    if layout == :tiles
      %(<div class="c-colour-example">#{intro}#{note}#{html}</div>)
    else
      %(<div class="c-colour-example">#{html}</div>\n#{note})
    end
  end

  def colour_example_tiles(root, id, level)
    root.css('figure').each_with_index.map do |figure, index|
      caption = figure.at_css('figcaption')
      title = caption.at_css('strong').text.strip
      names = caption.text.split('Colours:', 2).last.to_s.strip.delete_suffix('.').split(', ').map(&:strip)
      caption.remove
      figure.remove_attribute('aria-labelledby')
      figure.remove_attribute('style')
      swatches = colour_swatch_list(names.map { |name| colour_swatch(colour_id_by_name(name), key: "#{id}-#{index}") })
      %(<h#{level}>#{escape(title)}</h#{level}>\n<div class="c-pair c-pair--tile">#{figure.to_html.gsub(/^[ \t]+/, '')}<div class="c-pair__colours">#{swatches}</div></div>)
    end.join("\n")
  end

  # The record lists its colours with their jobs ("Primary blue: bars"). Show
  # them as GOV.UK's compact swatches, keeping each job as a note.
  def colour_example_chart(root, id)
    list = root.at_css('ul[data-govuk-colours]')
    heading = list&.previous_element
    if list
      items = list.css('li').map do |item|
        role = item.text.split(':', 2).last.to_s.strip
        colour_swatch(item['data-govuk-colour'], key: id, note: role)
      end
      heading.remove if heading&.name == 'h3'
      # Nokogiri's HTML4 parser rewrites <div> inside <dl>, so the swatch list
      # goes in as a placeholder and is substituted into the final string.
      @colour_example_swatches = %(<p><strong>Colours used</strong></p>) + colour_swatch_list(items, compact: true)
      list.replace(Nokogiri::XML::Text.new('COLOUR-EXAMPLE-SWATCHES', root.document))
    end
    colour_example_data_tables(root)
  end

  # Data tables stay on the page as the text alternative to the picture, in
  # a details element, so the picture leads as it does on GOV.UK.
  def colour_example_data_tables(root)
    root.css('.civica-table-scroll').each do |region|
      next unless region.at_css('table')
      label = region.at_css('caption')&.text&.strip
      summary = label && !label.empty? ? "Show the data: #{label}" : 'Show the data'
      details = Nokogiri::HTML::DocumentFragment.parse(%(<details class="govuk-details"><summary class="govuk-details__summary"><span class="govuk-details__summary-text">#{escape(summary)}</span></summary><div class="govuk-details__text"></div></details>)).at_css('details')
      region.add_next_sibling(details)
      # The layout gives every table one scrollable, labelled region, so the
      # record's own region wrapper is dropped to avoid 2 nested focus stops.
      details.at_css('.govuk-details__text').add_child(region.at_css('table'))
      region.remove
    end
  end

  def colour_callout
    %(<div class="govuk-inset-text c-callout">Indicative examples for illustrative purposes only.</div>)
  end

  # One polite status region per page announces every copy result. GOV.UK
  # shows the copy icons without an explanatory sentence, and so does civica.
  def colour_copy_status
    %(<p class="govuk-visually-hidden" role="status" data-copy-value-status></p>)
  end
end
