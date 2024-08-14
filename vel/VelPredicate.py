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
    

    def run_predicate(log_view, log, conditions, query_name):
        print(f"Running predicates for query: {query_name}")

        query_data = conditions.get(query_name)
        
        if not query_data:
            print(f"No data found for query: {query_name}")
            return

        query_name_value = query_data.get('query_name', '')
        condition_list = query_data.get('conditions', [])
        
        predicates = []

        for index, condition in enumerate(condition_list):
            predicate_class = condition.get('predicate_class')
            attribute_key = condition.get('attribute_key')
            values = condition.get('values')
            min_duration = condition.get('min_duration_seconds')
            max_duration = condition.get('max_duration_seconds')

            print(f"Condition {index + 1}:")
            print(f"Predicate: {predicate_class}")
            print(f"Attribute Key: {attribute_key}")
            print(f"Values: {values}")
            print(f"Min Duration: {min_duration}")
            print(f"Max Duration: {max_duration}")


            if attribute_key is not None and values is not None:
                predicate_instance = predicate_class(attribute_key, values)
            elif min_duration is not None and max_duration is not None:
                predicate_instance = predicate_class(min_duration, max_duration)
            else:
                predicate_instance = predicate_class(values)

            predicates.append(predicate_instance)

        query_instance = Query(query_name_value, predicates)
        print(f"Query Instance: {query_instance}")

        rs_no_p, comp_rs_no_p = log_view.evaluate_query(query_name_value, log, query_instance)

        print(f"Results for Query: {rs_no_p}")

        return rs_no_p 

   # def run_predicate(predicate_class, log_view, log, args):
    #     predicate = args.get('predicate')
    #     attribute_key = args.get('attribute_key')
    #     values = args.get('values')
    #     min_duration = args.get('min_duration')
    #     max_duration = args.get('max_duration')
        
    #     print('Running predicate:', predicate, attribute_key, values)

    #     if attribute_key is not None:
    #         predicate_instance = predicate_class(attribute_key, values)
    #     elif values is None:
    #         predicate_instance = predicate_class(min_duration, max_duration)
    #     else:
    #         predicate_instance = predicate_class(values)

    #     # will be changed while implementing registry
        
    #     query_no_p = Query('unpaid', [predicate_instance])

    #     rs_no_p, comp_rs_no_p = log_view.evaluate_query('rs_unpaid', log, query_no_p)



    #     return rs_no_p


        # query_no_p = Query('unpaid', [predicate_class(,)])
        # rs_no_p, complement_no_p = log_view.evaluate_query('rs_unpaid', log, query_no_p)
        # return predicate_class(log, *args)

    # def run_predicate(log_view, log, args):
    #     qname = args.get('query_name')
    #     predicates = args.get('predicate_class')
    #     attribute_keys = args.get('attribute_key')
    #     values_list = args.get('values')
    #     min_duration = args.get('min_duration')
    #     max_duration = args.get('max_duration')
        
    #     print('Running predicates:', predicates, attribute_keys, values_list)

 
    #     predicate_instances = []


    #     for predicate, attribute_key, values in zip(predicates, attribute_keys, values_list):
    #         if attribute_key is not None and values is not None:
    #             # predicate instance for attribute_key and values
    #             predicate_instance = predicate(attribute_key, values)
    #         elif values is None and min_duration is not None and max_duration is not None:
    #             # case for duration predicates
    #             predicate_instance = predicate(min_duration, max_duration)
    #         elif values is not None:
    #             # where there are only values without attribute keys
    #             predicate_instance = predicate(values)
    #         else:
    #             # If no valid combination is found, log the issue or raise an error
    #             raise ValueError(f"Invalid combination of predicate, attribute_key, and values: {predicate}, {attribute_key}, {values}")


    #         predicate_instances.append(predicate_instance)
    #         print("Predicate Instance :,,",predicate_instances, predicate, attribute_key, values)


    #     query = Query(qname, predicate_instances)


    #     # Evaluate the query using the log_view
    #     rs_no_p, comp_rs_no_p = log_view.evaluate_query(qname, log, query)

    #     return rs_no_p