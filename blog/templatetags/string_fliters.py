from django import template

register = template.Library()

class IDData:
    def __init__(self, id_type, ids):
        self.type = id_type
        self.ids = ids


@register.filter
def strip(value):
    if isinstance(value, str):
        return value.strip()
    return value

@register.filter
def split_ids(value):
    """
    将 'PDB:3EOA' 或 'EMBL Genbank:AJ249791/AJ249792'
    转为 {type: ..., ids: [...]}
    """
    if isinstance(value, str) and ':' in value:
        prefix, ids = value.split(':', 1)
        return {'type': prefix.strip(), 'ids': [x.strip() for x in ids.split('/')]}
    return {'type': 'Unknown', 'ids': []}

@register.filter
def startswith(value, arg):
    if isinstance(value, str):
        return value.lower().startswith(arg.lower())
    return False