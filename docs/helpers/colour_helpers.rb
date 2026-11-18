require 'json'
require 'yaml'
require 'digest'

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

  # The label on a sample is black or white, whichever contrasts more.
  def colour_label_hex(hex)
    colour_contrast(hex, '#0B0C0C') >= colour_contrast(hex, '#FFFFFF') ? '#0B0C0C' : '#FFFFFF'
  end

  # Home Assistant custom properties that the shipped civica theme sets to
  # exactly this value (light mode). Read from the generated theme, so the
  # list is never typed by hand and disappears if the theme stops using it.
  CIVICA_THEME_PROPERTIES = %w[primary-color primary-text-color secondary-text-color text-primary-color link-color
                               divider-color error-color success-color civica-input-border civica-focus-background
                               civica-focus-text card-background-color primary-background-color].freeze

  def civica_theme_tokens
    @civica_theme_tokens ||= begin
      theme = YAML.safe_load(File.read(File.expand_path('../themes/civica.yaml', root))).values.first
      light = theme.reject { |key, _| key == 'modes' }.merge(theme.dig('modes', 'light') || {})
      light.select { |key, value| CIVICA_THEME_PROPERTIES.include?(key) && value.is_a?(String) && value.start_with?('#') }
    end
  end

  def colour_theme_properties(hex)
    civica_theme_tokens.select { |_, value| value.casecmp?(hex) }.keys.sort.map { |key| "--#{key}" }
  end

  def colour_value_row(label, value, colour_name, copy: true)
    id = 'v-' + Digest::SHA1.hexdigest("#{colour_name}|#{label}|#{value}")[0, 10]
    button = copy ? %(<button type="button" class="c-copy-value" data-copy-value="#{escape(value)}" aria-label="Copy #{escape(label)} #{escape(value)} for #{escape(colour_name)}" hidden><svg class="c-copy-value__icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M5 1h8a2 2 0 0 1 2 2v8h-2V3H5z"/><path d="M1 5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2z"/></svg><span class="c-copy-value__text" aria-hidden="true">Copy</span></button>) : ''
    %(<div class="c-swatch__row"><dt>#{escape(label)}</dt><dd><code id="#{id}">#{escape(value)}</code>#{button}</dd></div>)
  end

  # One swatch. `fields` picks which codes to show: GOV.UK screen pages show
  # RGB and hex; the print page shows CMYK and Pantone only.
  def colour_swatch(id, fields: %i[hex rgb sass theme], role: nil)
    colour = govuk_colour(id)
    name = colour.fetch('name')
    hex = colour.fetch('hex')
    rows = []
    fields.each do |field|
      case field
      when :hex then rows << colour_value_row('Hex', hex, name)
      when :rgb then rows << colour_value_row('RGB', colour.fetch('rgb').join(' '), name)
      when :sass then rows << colour_value_row('Sass', colour['sass'], name) if colour['sass']
      when :cmyk then rows << colour_value_row('CMYK', colour.dig('print', 'cmyk').join(' '), name) if colour['print']
      when :pantone then rows << colour_value_row('Pantone', colour.dig('print', 'pantone'), name) if colour['print']
      when :theme
        colour_theme_properties(hex).each { |property| rows << colour_value_row('civica theme', "var(#{property})", name) }
      end
    end
    rows << %(<div class="c-swatch__row"><dt>Print</dt><dd>No print value given</dd></div>) if fields.include?(:cmyk) && !colour['print']
    sample = %(<span class="c-swatch__sample" style="background-color:#{hex};color:#{colour_label_hex(hex)}" aria-hidden="true">#{escape(name)}</span>)
    heading = role ? %(<p class="c-swatch__name">#{escape(role)}: #{escape(name)}</p>) : %(<p class="c-swatch__name">#{escape(name)}</p>)
    %(<li class="c-swatch">#{sample}#{heading}<dl class="c-swatch__codes">#{rows.join}</dl></li>)
  end

  def colour_swatches(ids, **options)
    %(<ul class="c-swatches" role="list">#{ids.map { |id| colour_swatch(id, **options) }.join}</ul>)
  end

  # A palette as GOV.UK groups it: one heading and one swatch list per group.
  def colour_palette(page, level: 3, **options)
    colour_page(page).fetch('palette').map do |group|
      %(<h#{level} id="#{colour_slug(group.fetch('title'))}">#{escape(group.fetch('title'))}</h#{level}>\n) + colour_swatches(group.fetch('colours'), **options)
    end.join("\n")
  end

  # Web functional colours: GOV.UK token name, its palette colour and codes.
  def colour_functional_tokens(level: 3)
    colour_page('web').fetch('functional').map do |group|
      items = group.fetch('tokens').map do |token|
        colour = govuk_colour(token.fetch('colour'))
        name = token.fetch('token')
        rows = [colour_value_row('Token', name, name), colour_value_row('Sass', %(govuk-functional-colour("#{name}")), name),
                colour_value_row('Hex', colour.fetch('hex'), name), colour_value_row('RGB', colour.fetch('rgb').join(' '), name)]
        colour_theme_properties(colour.fetch('hex')).each { |property| rows << colour_value_row('civica theme', "var(#{property})", name) }
        sample = %(<span class="c-swatch__sample" style="background-color:#{colour.fetch('hex')};color:#{colour_label_hex(colour.fetch('hex'))}" aria-hidden="true">#{escape(name)}</span>)
        %(<li class="c-swatch">#{sample}<p class="c-swatch__name">#{escape(name)} <span class="c-swatch__alias">(#{escape(colour.fetch('name'))})</span></p><dl class="c-swatch__codes">#{rows.join}</dl></li>)
      end
      %(<h#{level} id="functional-#{colour_slug(group.fetch('title'))}">#{escape(group.fetch('title'))}</h#{level}>\n<ul class="c-swatches" role="list">#{items.join}</ul>)
    end.join("\n")
  end

  # One polite status region per page announces every copy result.
  def colour_copy_status
    %(<p class="govuk-visually-hidden" role="status" data-copy-value-status></p>)
  end

  def colour_source_link(page)
    url = colour_page(page).fetch('url')
    %(<a href="#{url}">GOV.UK Brand Guidelines: #{escape(page.capitalize)}</a>)
  end
end
