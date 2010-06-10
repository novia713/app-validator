import re

import decorator

@decorator.register_test(tier=1)
def test_install_rdf_params(err,
                            package_contents=None,
                            xpi_package=None):
    """Tests to make sure that some of the values in install.rdf
    are not gummed up."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    if err.get_resource("listed"):
        shouldnt_exist = ("hidden")
    else:
        shouldnt_exist = ("updateURL",
                          "updateKey",
                          "hidden")
    obsolete = ("file")
    must_exist_once = ["id_",
                       "version",
                       "name",
                       "targetApplication"]
    may_exist_once = ["about", # For <Description> element
                      "type",
                      "optionsURL",
                      "aboutURL",
                      "iconURL",
                      "homepageURL",
                      "creator"]
    may_exist = ("targetApplication",
                 "localized",
                 "description",
                 "creator",
                 "translator",
                 "contributor",
                 "targetPlatform",
                 "requires",
                 "developer")
    
    banned_pattern = "Banned element %s exists in install.rdf."
    obsolete_pattern = "Obsolete element %s found in install.rdf."
    unrecognized_pattern = "Unrecognized element in install.rdf: %s"
    
    top_id = install.get_root_subject()
    
    for pred_raw in install.rdf.predicates(top_id, None):
        predicate = pred_raw.split("#").pop()
        
        # Some of the element names collide with built-in function
        # names of tuples/lists.
        if predicate == "id":
            predicate += "_"
        
        # Test if the predicate is banned
        if predicate in shouldnt_exist:
            err.error(banned_pattern % predicate,
                      """The detected element is not allowed in addons
                      under the configuration that you've specified."""
                      "install.rdf")
            continue
        
        # Test if the predicate is obsolete
        if predicate in obsolete:
            err.info(obsolete_pattern % predicate,
                     """The found element has not been banned, but it
                     is no longer supported by any modern Mozilla
                     product. Removing the element is recommended and
                     will not break support.""",
                     "install.rdf")
            continue
        
        # Remove the predicate from move_exist_once if it's there.
        if predicate in must_exist_once:
            
            object_value = install.get_object(None, pred_raw)
            
            # Test the predicate for specific values.
            if predicate == "id_":
                _test_id(err, object_value)
            elif predicate == "version":
                _test_version(err, object_value)
            
            must_exist_once.remove(predicate)
            continue
        
        # Do the same for may_exist_once.
        if predicate in may_exist_once:
            may_exist_once.remove(predicate)
            continue
        
        # If the element is safe for repetition, continue
        if predicate in may_exist:
            continue
        
        # If the predicate isn't in any of the above lists, it is
        # invalid and needs to go.
        err.error(unrecognized_pattern % predicate,
                  """The element that was found is not a part of the
                  install manifest specification, has been used too
                  many times, or is not applicable to the current
                  configuration.""",
                  "install.rdf")
        
    # Once all of the predicates have been tested, make sure there are
    # no mandatory elements that haven't been found.
    if must_exist_once:
        for predicate in must_exist_once:
            err.error("install.rdf is missing element: %s" % predicate,
                      """The element listed is a required element in
                      the install manifest specification. It must be
                      added to your addon.""",
                      "install.rdf")
    

def _test_id(err, value):
    "Tests an install.rdf GUID value"
    
    id_pattern = re.compile("(\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}|[a-z0-9-\._]*\@[a-z0-9-\._]+)")
    
    # Must be a valid version number.
    if not id_pattern.match(value):
        err.error("The value of <em:version> is invalid.",
                  """The values supplied for <em:version> in the
                  install.rdf file is not a valid version string.""",
                  "install.rdf")
    

def _test_version(err, value):
    "Tests an install.rdf version number"
    
    whitespace_pattern = re.compile(".*\s.*")
    version_pattern = re.compile("\d+(\+|\w+)?(\.\d+(\+|\w+)?)*")
    
    # Cannot have whitespace in the pattern.
    if whitespace_pattern.match(value):
        err.error("<em:version> value cannot contain whitespace.",
                  """In your addon's install.rdf file, version numbers
                  cannot contain whitespace characters of any kind.""",
                  "install.rdf")
    
    # Must be a valid version number.
    if not version_pattern.match(value):
        err.error("The value of <em:version> is invalid.",
                  """The values supplied for <em:version> in the
                  install.rdf file is not a valid version string.""",
                  "install.rdf")
    