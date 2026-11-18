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
  def colour_swatch(id, fields: %i[rgb hex], role: nil, name: nil, key: nil)
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
  def colour_group_links(page, extra = {})
    links = colour_page(page).fetch('palette').map { |group| [group.fetch('title').downcase, "##{colour_slug(group.fetch('title'))}"] } + extra.to_a
    %(<ul>#{links.map { |text, href| %(<li><a href="#{href}">#{escape(text)}</a></li>) }.join}</ul>)
  end

  # Chart categorical colours, in the GOV.UK order. Axes, lines and labels
  # carry their role in the name, as upstream shows them.
  def colour_chart_categorical(**options)
    colour_swatch_list(colour_page('charts').fetch('categorical').map { |item| colour_swatch(item.fetch('colour'), role: item['role'], **options) })
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

  # GOV.UK shows each colour example as a picture on the page, followed by
  # "Indicative examples for illustrative purposes only." The pictures come
  # from the same example record as the standalone example page, so there is
  # one source. Only the <figure> elements are taken: their headings and
  # tables belong to the standalone page.
  # `min` is the narrowest a picture may get before the grid wraps it.
  def colour_figures(id, min: nil)
    spec = config[:civica_examples].fetch(id) { raise "Unknown example #{id}" }
    figures = Nokogiri::HTML::DocumentFragment.parse(spec.fetch('html')).css('figure')
    raise "Example #{id} has no figure to show" if figures.empty?
    style = min ? %( style="--c-figure-min:#{min}") : ''
    # Indented lines would become Markdown code blocks, so drop the indentation.
    html = figures.map(&:to_html).join.gsub(/^[ \t]+/, '')
    %(<div class="c-colour-figures"#{style}>#{html}</div>\n#{colour_callout})
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
