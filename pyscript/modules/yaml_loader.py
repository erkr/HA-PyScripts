import yaml

# this extra class avoids we add the generic loader for others 
#@pyscript_compile
class YamlLoader(yaml.SafeLoader):
    pass

#@pyscript_compile
#def test_constructor(loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> str:
#   return f"!Test handled"

# source: https://death.andgravity.com/any-yaml#preserving-tags
# I only removed the extra Tagged class
# this callback must be defined synchronious so it can't be defined directly in a hass-pyscript
# Also the @pyscript_compile is needed 
@pyscript_compile    
def construct_undefined(self, node):
    if isinstance(node, yaml.nodes.ScalarNode):
        value = self.construct_scalar(node)
    elif isinstance(node, yaml.nodes.SequenceNode):
        value = self.construct_sequence(node)
    elif isinstance(node, yaml.nodes.MappingNode):
        value = self.construct_mapping(node)
    else:
        assert False, f"unexpected node: {node!r}"
    return f"{node.tag} {value}"

   
def yaml_loader():
   loader = YamlLoader
   #loader.add_constructor('!Test', test_constructor)
   loader.add_constructor(None, construct_undefined)
   return loader   
   