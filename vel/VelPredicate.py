import inspect
import logview
from logview.predicate import *
from logview.utils import LogViewBuilder

class VelPredicate:
    result_sets = {}

    def get_predicate_args(predicate_class):
        init_signature = inspect.signature(predicate_class.__init__)
        parameters = list(init_signature.parameters.keys())[1:]
         
        return parameters
    
    def run_predicate(log_view, conditions, query_name, n):
        """Evaluates the given conditions against the log and stores the results."""
         

         
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
            selected_log_name = selected_log_name[0] 
            print(f"Selected log: {selected_log_name}") 

        selected_log_dataframe = log_view.result_set_name_cache.get(selected_log_name)

        if selected_log_dataframe is None:
            return (f"No log data found for the selected log: {selected_log_name}")   

         
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
            print(f"Predicate Instance: {predicate_instance}, {predicates}")


        # for index, condition in enumerate(condition_list):
        #     predicate_class = condition.get('predicate_class')
        #     attribute_key = condition.get('attribute_key')
        #     values = condition.get('values')
        #     min_duration = condition.get('min_duration_seconds')
        #     max_duration = condition.get('max_duration_seconds')

             
             
            
             
        #     init_signature = inspect.signature(predicate_class.__init__)
        #     parameters = list(init_signature.parameters.keys())[1:]   

        #     args = []

        #     if 'attribute_key' in parameters and 'values' in parameters and attribute_key is not None and values is not None:
        #         args = [attribute_key, values]
        #     elif 'min_duration' in parameters and 'max_duration' in parameters and min_duration is not None and max_duration is not None:
        #         args = [min_duration, max_duration]
        #     elif 'values' in parameters and values is not None:
        #         args = [values]
        #     else:
        #         print(f"Unknown arguments for predicate class {predicate_class}.")

        #     if args:
        #         predicate_instance = predicate_class(*args)
        #         predicates.append(predicate_instance)
        #         print(f"Predicate Instance created: {predicate_instance}, predicates list: {predicates}")




        query_instance = Query(query_name_value, predicates)

        rs_no_p, comp_rs_no_p = log_view.evaluate_query(f'rs_{query_name_value}', selected_log_dataframe, query_instance)

         

        VelPredicate.result_sets.update({
            f'rs_{query_name_value}': rs_no_p,
            f'comp_rs_{query_name_value}': comp_rs_no_p
        })

        log_view.label_result_set(rs_no_p, label)
         

        if n == 0:
            return rs_no_p,len(rs_no_p['case:concept:name'].unique()),len(rs_no_p)
        else:
            return rs_no_p[:n],len(rs_no_p['case:concept:name'].unique()),len(rs_no_p)

    
    def apply_label_to_result(log_view, query_name, label):
        """Apply a label to the result set of a given query."""
        result_set = VelPredicate.result_sets.get(f'rs_{query_name}')
        if result_set is None:
             
            return

         
        log_view.label_result_set(result_set, label)
         


    @staticmethod
    def get_summary(log_view):
        """Fetches the summary of all registered queries using LogView's built-in method."""
        return log_view.get_summary(verbose=False)


