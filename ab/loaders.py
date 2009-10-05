from ab.middleware import get_current_request
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.loaders.filesystem import \
    load_template_source as default_template_loader
from django.utils.importlib import import_module

template_source_loaders = None

def load_template_source(template_name, template_dirs=None, 
    template_loader=default_template_loader):
    """If an Experiment exists for this template use template_loader to load it."""    
    request = get_current_request()
    test_template_name = request.ab.run(template_name)

    global template_source_loaders
    if template_source_loaders is None:
        loaders = []
        for path in settings.TEMPLATE_LOADERS:
            i = path.rfind('.')
            module, attr = path[:i], path[i+1:]
            try:
                mod = import_module(module)
            except ImportError, e:
                raise ImproperlyConfigured, 'Error importing template source loader %s: "%s"' % (module, e)
            try:
                func = getattr(mod, attr)
            except AttributeError:
                raise ImproperlyConfigured, 'Module "%s" does not define a "%s" callable template source loader' % (module, attr)
            if not func.is_usable:
                import warnings
                warnings.warn("Your TEMPLATE_LOADERS setting includes %r, but your Python installation doesn't support that type of template loading. Consider removing that line from TEMPLATE_LOADERS." % path)
            else:
                loaders.append(func)
        template_source_loaders = tuple(loaders)
    for template_loader in template_source_loaders:
        if template_loader != load_template_source:
            try:
                return template_loader(test_template_name, template_dirs=template_dirs)
            except TemplateDoesNotExist:
                pass
    raise TemplateDoesNotExist
load_template_source.is_usable = True
