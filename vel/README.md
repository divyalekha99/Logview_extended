
1. Overview:

This project is centered around the LogView framework for process mining and extends its functionality by creating a user interface (UI) to interact with the library. The main components are:

- LogView: A framework for process mining analysis.
- Vel.py: Contains the core logic to interact with the LogView library and build the UI components.
- VelPredicate.py: Implements specific predicates and conditions to be used within the LogView framework.
- velUi.ipynb: A Jupyter notebook demonstrating how to run the UI using the Vel class.


2. File Descriptions

2.1. Vel.py

This file contains the primary logic for creating the user interface (UI) for the LogView library. It uses Dash for the UI components and integrates several functionalities from LogView. Key features include:

Query Builder: Facilitates dynamic construction of queries against event logs


2.2 VelPredicate.py
This file defines the VelPredicate class, which handles predicates or conditions that can be applied within the LogView framework.

2.3 velUi.ipynb
This notebook demonstrates how to run the UI built using Vel.py. It includes setting up and running the server inline within the notebook.