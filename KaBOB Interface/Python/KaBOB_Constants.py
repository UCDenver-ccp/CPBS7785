"""
Constants for KaBOB Interface
"""

'''
SERVER INFORMATION
'''

HOST = "amc-tantor.ucdenver.pvt"
PORT = 10037
USER = None  # 'anonymous'
PASSWORD = None  # ''
CATALOG = ''
RELEASE = "kabob_prod_feb2018"
INSTANCE_RELEASE = "kabob_instance_prod_feb2018"

'''
NAMESPACES
'''

BIO_NAMESPACE = "ccp.ext"
ICE_NAMESPACE = "ccp.ext"

NAMESPACE_ASSOCIATIONS = {"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                          "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                          "owl": "http://www.w3.org/2002/07/owl#",
                          "obo": "http://purl.obolibrary.org/obo/",
                          "oboInOwl": "http://www.geneontology.org/formats/oboInOwl#",
                          "ccp.ext": "http://ccp.ucdenver.edu/obo/ext/",
                          "ccp.bnode": "http://ccp.ucdenver.edu/bnode/"}

'''
RELATIONS
'''

SUBCLASSOF = "rdfs:subClassOf"
LABEL = "rdfs:label"
PART_OF = "obo:BFO_0000050"
HAS_PART = "obo:BFO_0000051"
DENOTES = "obo:IAO_0000219"
HAS_PARTICIPANT = "obo:RO_0000057"
TRANSPORTS = "obo:RO_0002313"
CAUSES = "obo:RO_0003302"
TYPE = "rdf:type"
XREF = "oboInOwl:hasDbXref"
ID = "oboInOwl:id"
OBONAMESPACE = "oboInOwl:hasOBONamespace"
DEFINITION = "obo:IAO_0000115"
EXACTSYNONYM = "oboInOwl:hasExactSynonym"
COMMENT = "rdfs:comment"
EQUIVALENTCLASS = "owl:equivalentClass"
RESTRICTION_PROPERTY = "owl:onProperty"
RESTRICTION_VALUE = "owl:someValuesFrom"
INVERSE_OF = "owl:inverseOf"

RESTRICTION = "owl:Restriction"

# Ignore these relations when making slots

RELATIONS_TO_IGNORE = [TYPE,
                       SUBCLASSOF,
                       LABEL,
                       XREF,
                       ID,
                       DEFINITION,
                       EXACTSYNONYM,
                       COMMENT,
                       OBONAMESPACE,
                       EQUIVALENTCLASS,
                       DENOTES]


def get_namespace(namespace):
    return NAMESPACE_ASSOCIATIONS.get(namespace)


def get_full_uri(concise_name):
    namespace, localname = concise_name.split(":")
    return get_namespace(namespace) + localname
