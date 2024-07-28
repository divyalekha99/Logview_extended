import inspect
import logview
from logview.predicate import *
from logview.utils import LogViewBuilder

class VelPredicate:

    def get_predicate_args(predicate_class):
        init_signature = inspect.signature(predicate_class.__init__)
        parameters = list(init_signature.parameters.keys())[1:]
        print(parameters)
        return parameters
    
    def run_predicate(predicate_class, log_view, log, args):
        predicate = args.get('predicate')
        attribute_key = args.get('attribute_key')
        values = args.get('values')
        min_duration = args.get('min_duration')
        max_duration = args.get('max_duration')
        
        print('Running predicate:', predicate, attribute_key, values)

        if attribute_key is not None:
            predicate_instance = predicate_class(attribute_key, values)
        elif values is None:
            predicate_instance = predicate_class(min_duration, max_duration)
        else:
            predicate_instance = predicate_class(values)

        # will be changed while implementing registry
        
        query_no_p = Query('unpaid', [predicate_instance])

        rs_no_p, comp_rs_no_p = log_view.evaluate_query('rs_unpaid', log, query_no_p)



        return rs_no_p


        # query_no_p = Query('unpaid', [predicate_class(,)])
        # rs_no_p, complement_no_p = log_view.evaluate_query('rs_unpaid', log, query_no_p)
        # return predicate_class(log, *args)