import inspect
import logview
from logview.predicate import *
from logview.utils import LogViewBuilder

class VelPredicate:
    result_sets = {}

    def get_predicate_args(predicate_class):
        init_signature = inspect.signature(predicate_class.__init__)
        parameters = list(init_signature.parameters.keys())[1:]
        print(parameters)
        return parameters
    
    def run_predicate(log_view, conditions, query_name):
        """Evaluates the given conditions against the log and stores the results."""
        print(f"Running predicates for query: {query_name}, conditions: {conditions}")

        # Retrieve query data based on the query name
        query_data = conditions.get(query_name)

        if not query_data:
            print(f"No data found for query: {query_name}")
            return

        query_name_value = query_data.get('query_name', '')
        label = query_data.get('label', '')
        selected_log_name = query_data.get('source_log', '')
        condition_list = query_data.get('conditions', [])
        
        predicates = []

        if isinstance(selected_log_name, list):
            selected_log_name = selected_log_name[0]  # Handling if it's a list
        selected_log_dataframe = log_view.result_set_name_cache.get(selected_log_name)

        if selected_log_dataframe is None:
            return (f"No log data found for the selected log: {selected_log_name}")  # Return an empty DataFrame if not found

        # Create predicate instances based on user input
        for index, condition in enumerate(condition_list):
            predicate_class = condition.get('predicate_class')
            attribute_key = condition.get('attribute_key')
            values = condition.get('values')
            min_duration = condition.get('min_duration_seconds')
            max_duration = condition.get('max_duration_seconds')

            # Instantiate the predicate based on the available arguments
            if attribute_key is not None and values is not None:
                predicate_instance = predicate_class(attribute_key, values)
            elif min_duration is not None and max_duration is not None:
                predicate_instance = predicate_class(min_duration, max_duration)
            else:
                predicate_instance = predicate_class(values)

            predicates.append(predicate_instance)

        # Create a Query instance based on the query name and predicates
        query_instance = Query(query_name_value, predicates)

        # Evaluate the query against the log data
        rs_no_p, comp_rs_no_p = log_view.evaluate_query(f'rs_{query_name_value}', selected_log_dataframe, query_instance)

        # Store the result sets in the result_sets dictionary (optional, for your use case)
        VelPredicate.result_sets.update({
            f'rs_{query_name_value}': rs_no_p,
            f'comp_rs_{query_name_value}': comp_rs_no_p
        })

        log_view.label_result_set(rs_no_p, label)
        print(f"Applied label '{label}' to result set for query: {query_name}, and log{selected_log_name}") 
        # Return the primary result set
        # return VelPredicate.result_sets[f'rs_{query_name_value}'],
        return rs_no_p

    
    def apply_label_to_result(log_view, query_name, label):
        """Apply a label to the result set of a given query."""
        result_set = VelPredicate.result_sets.get(f'rs_{query_name}')
        if result_set is None:
            print(f"No result set found for query: {query_name}")
            return

        # Apply the label to the result set using the log_view's labeling function
        log_view.label_result_set(result_set, label)
        print(f"Applied label '{label}' to result set for query: {query_name}")


    @staticmethod
    def get_summary(log_view):
        """Fetches the summary of all registered queries using LogView's built-in method."""
        return log_view.get_summary(verbose=False)



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