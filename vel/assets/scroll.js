document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        const parentContainer = document.querySelector(".app-container");
        if (!parentContainer) {
            console.error("Parent container not found!");
            return;
        }

        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                 
                mutation.addedNodes.forEach(function (node) {
                    const conditionContainer = node.getElementsByClassName('condition-container')[0] || node.closest('.condition-container');
                    if (conditionContainer) {
                        conditionContainer.scrollTop = conditionContainer.scrollHeight;
                    } else {
                        console.log("Non-condition node added:", node);
                    }
                });

                 
                mutation.removedNodes.forEach(function (node) {
                    const conditionContainer = node.getElementsByClassName('condition-container')[0] || node.closest('.condition-container');
                    if (conditionContainer) {
                        conditionContainer.scrollTop = conditionContainer.minHeight;
                    }
                });
            });
        });

        observer.observe(parentContainer, { childList: true, subtree: true });
    }, 1000);
});

window.removeCondition = function(n_clicks_list, conditions, condition_count) {
    console.log("Remove condition function called with conditions: ", conditions);
    console.log("n_clicks_list: ", n_clicks_list);

     
    if (conditions.length === 0) {
        console.log("No conditions exist");
        return [conditions, condition_count];
    }

     
    for (let i = 0; i < n_clicks_list.length; i++) {
        if (n_clicks_list[i] > 0) {
            console.log("Condition remove button clicked, index: ", i);

             
            let condition_id_to_remove = i;   

             
            let condition_elements = document.querySelectorAll('.condition-container');
            let condition_ids = Array.from(condition_elements).map((el) => {
                const condition_id_element = el.querySelector('[id^="condition-"]');
                if (condition_id_element) {
                     
                    const condition_id = parseInt(condition_id_element.id.split('-')[1], 10);
                    return condition_id;
                }
                return null;   
            }).filter(id => id !== null);   

            console.log("Current condition IDs: ", condition_ids);

             
            let index_to_remove = condition_ids.indexOf(condition_id_to_remove);

            if (index_to_remove !== -1) {
                console.log("Removing condition at position: ", index_to_remove);

                 
                condition_elements[index_to_remove].remove();

                 
                conditions.splice(index_to_remove, 1);
            } else {
                console.log("Condition ID not found in the current list");
            }

            break;  
        }
    }

     
    return [conditions, condition_count];
};
