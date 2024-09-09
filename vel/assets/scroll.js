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
            });
        });
         
        observer.observe(parentContainer, { childList: true, subtree: true });

    }, 1000);   
});
