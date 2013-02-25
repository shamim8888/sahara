import logging
from eho.server.storage.models import *
from eho.server.storage.storage import db


def create_node_process(name, properties):
    """
    Creates new node process and node process properties
    :param name: process name
    :param properties: array of triples (name, required, default)
    :return: created node process
    """
    process = NodeProcess(name)
    db.session.add(process)
    db.session.commit()
    for p in properties:
        prop = NodeProcessProperty(process.id, p[0], p[1], p[2])
        db.session.add(prop)
    db.session.commit()
    return process


def create_node_type(name, processes):
    """
    Creates new node type using specified list of processes
    :param name:
    :param processes:
    :return:
    """
    node_type = NodeType(name)
    node_type.processes = processes
    db.session.add(node_type)
    db.session.commit()
    return node_type


def create_node_template(name, node_type_id, tenant_id, flavor_id, configs):
    """
    Creates new node templates
    :param name: template name
    :param node_type_id: node type
    :param tenant_id: tenant
    :param flavor_id: flavor
    :param configs: dict of process->property->value
    :return: created node template
    """
    node_template = NodeTemplate(name, node_type_id, tenant_id, flavor_id)
    db.session.add(node_template)
    for process_name in configs:
        process = NodeProcess.query.filter_by(name=process_name).first()
        conf = configs.get(process_name)
        for prop in process.node_process_properties:
            val = conf.get(prop.name, None)
            if not val and prop.required:
                if not prop.default:
                    raise RuntimeError('Template \'%s\', value missed '
                                       'for required param: %s %s'
                                       % (name, process.name, prop.name))
                val = prop.default
            db.session.add(NodeTemplateConfig(node_template.id, prop.id, val))
    db.session.commit()

    return node_template


def create_cluster(name, base_image_id, tenant_id, templates):
    """
    Creates new cluster
    :param name: cluster name
    :param base_image_id: base image
    :param tenant_id: tenant
    :param templates: dict of template->count
    :return: created cluster
    """
    cluster = Cluster(name, base_image_id, tenant_id)
    db.session.add(cluster)
    for template in templates:
        count = templates.get(template)
        cnc = ClusterNodeCount(cluster.id,
                               NodeTemplate.query.filter_by(name=template)
                               .first().id, int(count))
        db.session.add(cnc)
    db.session.commit()

    return cluster


def setup_defaults(app):
    nt_jt_nn = None
    nt_jt = None
    nt_nn = None
    nt_tt_dn = None

    if app.config.get('RESET_DB', False):
        # setup default processes
        p_jt = create_node_process('job_tracker', [('heap_size', True, None)])
        p_nn = create_node_process('name_node', [('heap_size', True, None)])
        p_tt = create_node_process('task_tracker', [('heap_size', True, None)])
        p_dn = create_node_process('data_node', [('heap_size', True, None)])

        for p in [p_jt, p_nn, p_tt, p_dn]:
            logging.info('New NodeProcess has been created: %s \'%s\'',
                         p.id, p.name)

        # setup default node types
        nt_jt_nn = create_node_type('JT+NN', [p_jt, p_nn])
        nt_jt = create_node_type('JT', [p_jt])
        nt_nn = create_node_type('NN', [p_nn])
        nt_tt_dn = create_node_type('TT+DN', [p_tt, p_dn])

        for nt in [nt_jt_nn, nt_jt, nt_nn, nt_tt_dn]:
            logging.info('New NodeType has been created: %s \'%s\' %s',
                         nt.id, nt.name,
                         [p.name.__str__() for p in nt.processes])

        logging.info('All defaults has been inserted')

    if app.config.get('STUB_DATA', False):
        jt_nn_large = create_node_template('jt_nn.large', nt_jt_nn.id, 't_1',
                                           'm1.large',
                                           {
                                               'job_tracker': {
                                                   'heap_size': '3072'
                                               },
                                               'name_node': {
                                                   'heap_size': '3072'
                                               }
                                           })
        jt_nn_xlarge = create_node_template('jt_nn.xlarge', nt_jt_nn.id, 't_1',
                                            'm1.xlarge',
                                            {
                                                'job_tracker': {
                                                    'heap_size': '6144'
                                                },
                                                'name_node': {
                                                    'heap_size': '6144'
                                                }
                                            })
        jt_large = create_node_template('jt.large', nt_jt.id, 't_1',
                                        'm1.large',
                                        {
                                            'job_tracker': {
                                                'heap_size': '3072'
                                            }
                                        })
        jt_xlarge = create_node_template('jt.xlarge', nt_jt.id, 't_1',
                                         'm1.xlarge',
                                         {
                                             'job_tracker': {
                                                 'heap_size': '6144'
                                             }
                                         })
        nn_large = create_node_template('nn.large', nt_nn.id, 't_1',
                                        'm1.large',
                                        {
                                            'name_node': {
                                                'heap_size': '3072'
                                            }
                                        })
        nn_xlarge = create_node_template('nn.xlarge', nt_nn.id, 't_1',
                                         'm1.xlarge',
                                         {
                                             'name_node': {
                                                 'heap_size': '6144'
                                             }
                                         })

        tt_dn_medium = create_node_template('tt_dn.medium', nt_tt_dn.id, 't_1',
                                            'm1.medium',
                                            {
                                                'task_tracker': {
                                                    'heap_size': '1536'
                                                },
                                                'data_node': {
                                                    'heap_size': '1536'
                                                }
                                            })
        tt_dn_large = create_node_template('tt_dn.large', nt_tt_dn.id, 't_1',
                                           'm1.large',
                                           {
                                               'task_tracker': {
                                                   'heap_size': '3072'
                                               },
                                               'data_node': {
                                                   'heap_size': '3072'
                                               }
                                           })
        tt_dn_xlarge = create_node_template('tt_dn.xlarge', nt_tt_dn.id, 't_1',
                                            'm1.xlarge',
                                            {
                                                'task_tracker': {
                                                    'heap_size': '6144'
                                                },
                                                'data_node': {
                                                    'heap_size': '6144'
                                                }
                                            })

        # cluster = create_cluster('cluster_1', 'base_image_1', 'tenant_1', {
        # 'jt+nn': 1,
        # 'tt+dn': 5
        # })
