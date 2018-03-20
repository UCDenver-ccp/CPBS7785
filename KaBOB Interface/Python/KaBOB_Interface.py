import logging
import warnings

from franz.openrdf.model import Literal
from franz.openrdf.model import URI
from franz.openrdf.sail.allegrographserver import AllegroGraphServer
from franz.openrdf.repository.repository import Repository
from franz.openrdf.connect import ag_connect

from MOPs import MOPsManager
import KaBOB_Constants

logging.basicConfig(level=logging.DEBUG)


class InstanceAndSuperClassesException(Warning):
    pass


class KaBOBInterface:
    log = logging.getLogger('KaBOBInterface')

    def __init__(self, conn):
        self.mopsManager = MOPsManager()
        self.kabob = conn
        [conn.setNamespace(name, value) for name, value in KaBOB_Constants.NAMESPACE_ASSOCIATIONS.items()]
        self.role_fillers = {}

    def mopify(self, node, depth):
        node = node if isinstance(node, URI) or isinstance(node, Literal) else self.create_uri(node)

        name = self.instance_name(node) if self.is_bio_instance(node) else self.node_print_name(node)

        self.log.debug("\t" * depth + "Mopifying " + name)

        slots = {self.node_print_name(statement.getPredicate()): self.node_print_name(statement.getObject())
                 for statement in self.agraph_get_objects(s=node, p=None, full_statement=True)}
        superclasses = self.get_superclasses(node)
        parents = []

        for superclass in superclasses:
            if self.is_restriction(superclass):
                slots[self.role_name(self.restriction_property(superclass))] = self.find_or_mopify(superclass, depth+1)
            else:
                parents.append(superclass)

        if parents and self.is_bio_instance(node):
            warnings.warn(name + " has both superclasses and type")

        parents = [self.find_or_mopify(parent, depth + 1) for parent in parents]
        mop = self.mopsManager.add_instance(name, parents, slots, _id=node) if self.is_bio_instance(
            node) else self.mopsManager.add_mop(name, parents, slots, _id=node)
        self.infer_inverse_relations(mop, slots)

        self.log.debug("\t" * depth + "Finished mopifying " + name)
        return mop

    def is_bio_instance(self, node):
        return self.is_bio(node) and self.get_node_type(node)

    @staticmethod
    def is_bio(node):
        return node.getNamespace() == KaBOB_Constants.get_namespace(KaBOB_Constants.BIO_NAMESPACE)

    @staticmethod
    def is_ice(node):
        return node.getNamespace() == KaBOB_Constants.get_namespace(KaBOB_Constants.ICE_NAMESPACE)

    def instance_name(self, node):
        return "%s - " % self.node_print_name(self.get_node_type(node))

    def node_print_name(self, node):
        labels = [o.getLabel() for o in self.agraph_get_objects(s=node, p=KaBOB_Constants.LABEL)]
        _id = self.agraph_get_object(s=node, p=KaBOB_Constants.ID)
        local_name = node.getLocalName() if isinstance(node, URI) else node

        def find_lowercase_label(_labels):
            for label in _labels:
                if label.islower():
                    return label
            return False

        if labels:
            return find_lowercase_label(labels) or labels[0]
        if _id:
            return _id.getLabel()
            # return _id or part_to_string(node, format="concise")
        else:
            return local_name

    def agraph_get_objects(self, s, p, full_statement=False):
        s = s if not s or isinstance(s, URI) or isinstance(s, Literal) else self.create_uri(s)
        p = p if not p or isinstance(p, URI) or isinstance(p, Literal) else self.create_uri(p)
        statements = self.agraph_get_statements(s=s, p=p)
        return statements if not statements or full_statement else [statement.getObject() for statement in statements]

    def agraph_get_statements(self, s=None, p=None, o=None):
        with self.kabob.getStatements(subject=s, predicate=p, object=o) as statements:
            return statements.asList()

    def agraph_get_object(self, s, p):
        objects = self.agraph_get_objects(s, p)
        return objects[0] if objects else None

    def agraph_get_subjects(self, o, p, full_statement=False):
        o = o if not o or isinstance(o, URI) or isinstance(o, Literal) else self.create_uri(o)
        p = p if not p or isinstance(p, URI) or isinstance(p, Literal) else self.create_uri(p)
        statements = self.agraph_get_statements(o=o, p=p)
        return statements if not statements or full_statement else [statement.getSubject() for statement in statements]

    def agraph_get_subject(self, o, p):
        subjects = self.agraph_get_subjects(o, p)
        return subjects[0] if subjects else None

    def get_superclasses(self, node):
        return self.agraph_get_objects(s=node, p=KaBOB_Constants.SUBCLASSOF)

    def is_restriction(self, node):
        _type = self.get_node_type(node)
        return _type and _type.getURI() == KaBOB_Constants.get_full_uri(KaBOB_Constants.RESTRICTION)

    def get_node_type(self, node):
        return self.agraph_get_object(s=node, p=KaBOB_Constants.TYPE)

    def role_name(self, node):
        return self.node_print_name(node)

    def restriction_property(self, node):
        return self.agraph_get_object(s=node, p=KaBOB_Constants.RESTRICTION_PROPERTY)

    def find_or_mopify(self, node, depth):
        return self.find_mop(node) or self.mopify(node, depth)

    def find_mop(self, node):
        return self.mopsManager.get_frame(node)

    def create_uri(self, name):
        namespace, localname = self.split_name(name)
        return self.kabob.createURI(namespace=namespace, localname=localname) if localname else self.kabob.createURI(
            name)

    @staticmethod
    def split_name(name):
        namespace, localname = name.split(":")
        namespace = KaBOB_Constants.get_namespace(namespace)
        return (namespace, localname) if namespace else (name, None)

    def bio(self, node):
        if self.is_ice(node):
            return self.ice_to_bio(node)
        else:
            subjects = self.agraph_get_subjects(o=node, p=KaBOB_Constants.DENOTES)
            for subject in subjects:
                if self.is_ice(subject):
                    return self.ice_to_bio(subject)

    def ice_to_bio(self, node):
        objects = self.agraph_get_objects(s=node, p=KaBOB_Constants.DENOTES)
        for _object in objects:
            if self.is_bio(_object):
                return _object

    def statement_to_slot(self, statement):
        pass

    def infer_inverse_relations(self, mop, slots):
        pass


class OpenKaBOB:
    log = logging.getLogger('OpenKaBOB')

    def __init__(self):
        self.kabob = None
        self.kabob_repository = None

    def connect_to_kabob(self):
        self.log.debug("Connecting to AllegroGraph server --" +
                       "host:'%s' port:%s" % (KaBOB_Constants.HOST, KaBOB_Constants.PORT))
        kabob_server = AllegroGraphServer(KaBOB_Constants.HOST, KaBOB_Constants.PORT,
                                          KaBOB_Constants.USER, KaBOB_Constants.PASSWORD)

        if KaBOB_Constants.CATALOG in kabob_server.listCatalogs() or KaBOB_Constants.CATALOG == '':
            kabob_catalog = kabob_server.openCatalog(KaBOB_Constants.CATALOG)

            if KaBOB_Constants.RELEASE in kabob_catalog.listRepositories():
                mode = Repository.OPEN
                self.kabob_repository = kabob_catalog.getRepository(KaBOB_Constants.RELEASE, mode)
                self.kabob = self.kabob_repository.getConnection()

                # print('Repository %s is up!' % self.kabob_repository.getDatabaseName())
                # print('It contains %d statement(s).' % self.kabob.size())
            else:
                print('%s does not exist' % KaBOB_Constants.RELEASE)
                print("Available repositories in catalog '%s':" % kabob_catalog.getName())
                for repo_name in kabob_catalog.listRepositories():
                    print('  - ' + repo_name)

        else:
            print('%s does not exist' % KaBOB_Constants.CATALOG)
            print('Available catalogs:')
            for cat_name in kabob_server.listCatalogs():
                if cat_name is None:
                    print('  - <root catalog>')
                else:
                    print('  - ' + str(cat_name))

    # Potentially better alternate method
    def alt_connect_to_kabob(self):
        self.kabob = ag_connect(KaBOB_Constants.RELEASE,
                                host=KaBOB_Constants.HOST,
                                port=KaBOB_Constants.PORT,
                                user=KaBOB_Constants.USER,
                                password=KaBOB_Constants.PASSWORD,
                                create=False,
                                clear=False)

        print('Statements in KaBOB:', self.kabob.size())

    def close_kabob(self):
        self.kabob.close()
        self.kabob_repository.shutDown()
        self.log.debug("Closed %s" % self.kabob_repository.getDatabaseName())

    def __enter__(self):
        self.connect_to_kabob()
        return self.kabob

    def __exit__(self, t, value, traceback):
        self.close_kabob()
