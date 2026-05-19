"""
Django template tags for CRM reusable components

Usage in templates:
{% load crm_components %}

{% button text='Click Me' variant='primary' %}
{% card header_title='My Card' %}
{% alert message='Success!' type='success' %}
{% badge text='Active' type='success' %}
{% empty_state title='No data' message='Add your first item' %}
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('components/_button.html')
def button(text, variant='primary', type='button', size='md', disabled=False, 
           loading=False, icon='', classes='', id='', onclick=''):
    """
    Render a button component
    
    Args:
        text: Button text
        variant: primary|secondary|danger|ghost
        type: button|submit|reset
        size: sm|md|lg
        disabled: Boolean
        loading: Boolean
        icon: SVG icon HTML
        classes: Additional CSS classes
        id: Button ID
        onclick: JavaScript onclick handler
    """
    return {
        'text': text,
        'variant': variant,
        'type': type,
        'size': size,
        'disabled': disabled,
        'loading': loading,
        'icon': mark_safe(icon) if icon else '',
        'classes': classes,
        'id': id,
        'onclick': onclick,
    }


@register.inclusion_tag('components/_card.html')
def card(header_title='', header_actions='', body_content='', footer_content='',
         hover=True, padding='md', classes=''):
    """
    Render a card component
    
    Args:
        header_title: Card header title
        header_actions: HTML for header action buttons
        body_content: Card body content
        footer_content: Card footer content
        hover: Enable hover effect
        padding: sm|md|lg
        classes: Additional CSS classes
    """
    return {
        'header_title': header_title,
        'header_actions': mark_safe(header_actions) if header_actions else '',
        'body_content': mark_safe(body_content) if body_content else '',
        'footer_content': mark_safe(footer_content) if footer_content else '',
        'hover': hover,
        'padding': padding,
        'classes': classes,
    }


@register.inclusion_tag('components/_modal.html')
def modal(modal_id, title='', body_content='', footer_content='', size='md',
          close_on_backdrop=True, type='default'):
    """
    Render a modal component
    
    Args:
        modal_id: Unique modal ID (required)
        title: Modal title
        body_content: Modal body content
        footer_content: Modal footer with action buttons
        size: sm|md|lg|xl
        close_on_backdrop: Close modal when clicking backdrop
        type: default|confirmation|alert
    """
    return {
        'modal_id': modal_id,
        'title': title,
        'body_content': mark_safe(body_content) if body_content else '',
        'footer_content': mark_safe(footer_content) if footer_content else '',
        'size': size,
        'close_on_backdrop': close_on_backdrop,
        'type': type,
    }


@register.inclusion_tag('components/_alert.html')
def alert(message, type='info', dismissible=True, icon=True, classes=''):
    """
    Render an alert component
    
    Args:
        message: Alert message text
        type: success|error|warning|info
        dismissible: Show dismiss button
        icon: Show icon
        classes: Additional CSS classes
    """
    return {
        'message': message,
        'type': type,
        'dismissible': dismissible,
        'icon': icon,
        'classes': classes,
    }


@register.inclusion_tag('components/_badge.html')
def badge(text, type='gray', size='md', rounded=True, classes=''):
    """
    Render a badge component
    
    Args:
        text: Badge text
        type: success|error|warning|info|primary|secondary|gray|active|inactive|
              prospeccion|calificacion|propuesta|negociacion|cierre_ganado|cierre_perdido
        size: sm|md|lg
        rounded: Boolean for pill shape
        classes: Additional CSS classes
    """
    return {
        'text': text,
        'type': type,
        'size': size,
        'rounded': rounded,
        'classes': classes,
    }


@register.inclusion_tag('components/_pagination.html', takes_context=True)
def pagination(context, page_obj, page_sizes='15,30,50', show_page_size=True,
               show_info=True, classes=''):
    """
    Render a pagination component
    
    Args:
        page_obj: Django paginator page object
        page_sizes: Comma-separated page size options
        show_page_size: Show page size selector
        show_info: Show "Showing X to Y of Z" info
        classes: Additional CSS classes
    """
    return {
        'page_obj': page_obj,
        'page_sizes': [s.strip() for s in page_sizes.split(',')],
        'show_page_size': show_page_size,
        'show_info': show_info,
        'classes': classes,
        'request': context.get('request'),
    }


@register.inclusion_tag('components/_empty_state.html')
def empty_state(title, message='', icon='', cta_text='', cta_url='',
                cta_onclick='', classes=''):
    """
    Render an empty state component
    
    Args:
        title: Main heading
        message: Descriptive message
        icon: SVG icon HTML
        cta_text: Call-to-action button text
        cta_url: Call-to-action button URL
        cta_onclick: JavaScript onclick handler
        classes: Additional CSS classes
    """
    return {
        'title': title,
        'message': message,
        'icon': mark_safe(icon) if icon else '',
        'cta_text': cta_text,
        'cta_url': cta_url,
        'cta_onclick': cta_onclick,
        'classes': classes,
    }


@register.inclusion_tag('components/_search_bar.html', takes_context=True)
def search_bar(context, placeholder='Buscar...', name='search', value='',
               autocomplete_url='', show_filters=False, filters_target='', classes=''):
    """
    Render a search bar component
    
    Args:
        placeholder: Search input placeholder
        name: Input name attribute
        value: Current search value
        autocomplete_url: URL for autocomplete suggestions
        show_filters: Show advanced filters button
        filters_target: ID of filters container to toggle
        classes: Additional CSS classes
    """
    return {
        'placeholder': placeholder,
        'name': name,
        'value': value,
        'autocomplete_url': autocomplete_url,
        'show_filters': show_filters,
        'filters_target': filters_target,
        'classes': classes,
        'request': context.get('request'),
    }


@register.inclusion_tag('components/_input.html')
def input_field(name, label, type='text', value='', placeholder='', required=False,
                disabled=False, readonly=False, error='', success='', help_text='',
                autocomplete='', pattern='', min='', max='', maxlength='',
                rows=4, classes=''):
    """
    Render an input component with floating label
    
    Args:
        name: Input name attribute
        label: Floating label text
        type: text|email|password|number|date|tel|url|textarea
        value: Input value
        placeholder: Placeholder text
        required: Boolean
        disabled: Boolean
        readonly: Boolean
        error: Error message or list of errors
        success: Success message
        help_text: Help text below input
        autocomplete: Autocomplete attribute
        pattern: Validation pattern
        min: Min value for number/date
        max: Max value for number/date
        maxlength: Max length for text
        rows: Number of rows for textarea
        classes: Additional CSS classes
    """
    return {
        'name': name,
        'label': label,
        'type': type,
        'value': value,
        'placeholder': placeholder,
        'required': required,
        'disabled': disabled,
        'readonly': readonly,
        'error': error,
        'success': success,
        'help_text': help_text,
        'autocomplete': autocomplete,
        'pattern': pattern,
        'min': min,
        'max': max,
        'maxlength': maxlength,
        'rows': rows,
        'classes': classes,
    }


@register.inclusion_tag('components/_table.html')
def data_table(headers, rows, sortable=True, loading=False, empty_message='No hay datos disponibles',
               striped=True, hover=True, responsive=True):
    """
    Render an advanced table component
    
    Args:
        headers: List of dicts with 'label', 'key', 'sortable' keys
        rows: List of data rows (list of dicts or objects)
        sortable: Enable sortable columns
        loading: Show loading skeleton
        empty_message: Message when no data
        striped: Alternate row colors
        hover: Enable row hover effect
        responsive: Enable horizontal scroll on mobile
    """
    return {
        'headers': headers,
        'rows': rows,
        'sortable': sortable,
        'loading': loading,
        'empty_message': empty_message,
        'striped': striped,
        'hover': hover,
        'responsive': responsive,
    }


@register.inclusion_tag('components/_sidebar.html', takes_context=True)
def sidebar(context, menu_items, collapsed=False, classes=''):
    """
    Render a sidebar component
    
    Args:
        menu_items: List of menu item dicts with 'label', 'url', 'icon', 'roles' keys
        collapsed: Initial collapsed state
        classes: Additional CSS classes
    """
    return {
        'menu_items': menu_items,
        'user': context.get('user'),
        'request': context.get('request'),
        'collapsed': collapsed,
        'classes': classes,
    }


# Custom template filters
@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def attr(obj, attribute):
    """Get attribute from object"""
    try:
        return getattr(obj, attribute, '')
    except (AttributeError, TypeError):
        return ''
