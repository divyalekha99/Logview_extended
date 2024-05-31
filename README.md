[![GPL-3.0 License](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="320" height="160">
  </a>
</div>

## About the project
We present **LogView**, a framework that helps process analysts validate the results of their queries and incrementally improve their knowledge of a log as they analyze it.
LogView keeps a record of the evaluated queries and results, and facilitates the comparison of different results with the intention of facilitating the analyst's understanding of the data.
We have implemented it as a Python library to help you integrate it into your existing process mining environments.

We provide an extensive tutorial and an analysis on the [Road Traffic Fine Management event log](https://data.4tu.nl/articles/dataset/Road_Traffic_Fine_Management_Process/12683249?file=24018146) in [notebooks](https://github.com/blindreview-logview123/logview/tree/main/notebooks).


<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites
LogView can be installed on Python 3.9.x / 3.10.x / 3.11.x / 3.12.x.

This is an example of how to create a conda environment with python 3.10 in case you don't have one:
*
    ```sh
    conda create -n logview_env python=3.10
    conda activate logview_env
    ```

### Installation

LogView hasn't been uploaded to the Python Package Index yet.
However, there's no need to worry! We can easily guide you through installing it locally in just two simple steps.

1. Clone the repo
   ```sh
   git clone https://github.com/blindreview-logview123/logview.git
   cd logview
   ```
2. Install LogView
   ```sh
   python setup.py sdist bdist_wheel
   pip install .
   ```

If you wish to execute the examples in the notebook files, please ensure that you have 'ipykernel' installed in your Python environment.
If it's not install, you can easily install it as follows:

* install `ipykernel` with pip
    ```sh
    conda activate logview_env
    pip install ipykernel
    ```

### Import ###
Once installed, you can import LogView into their Python scripts or Jupyter Notebooks:
```python
import logview
```
<!-- USAGE FEATURES -->
## Key Features ##

- Querying Logs: LogView allows users to execute queries on event logs to extract relevant information.
- Record of Evaluated Queries and Results: LogView keeps a record of the queries executed and their corresponding results, facilitating traceability and reproducibility.
- Result Characterization: LogView provides plugins to characterize the results of a query along multiple dimensions.
- Result Comparison: LogView provides plugins to compare different query results, aiding analysts in understanding the relationships among results produced by different queries.
- Result Visualization: LogView provides plugins to visualize multiple result sets and their overlaps.

<!-- USAGE EXAMPLES -->
## Usage Examples ##

In the example below, we show how to create a _logview_ object for your analysis and to run your first query.

```python
from logview.utils import LogViewBuilder
log = ... #your reading logic for log files using pm4py
log_view = LogViewBuilder.build_log_view(log)

from logview.predicate import *
query = Query('my_query', [EqToConstant('Activity', 'Send for Credit Collection')])
result_set_query, complement_query = log_view.evaluate_query('traces_with_scc', log, query)
```
_For more detailed examples, please refer to our *Notbooks* section and folder_

<!-- NOTEBOOKS -->
## Notebooks
For a detailed tutorial on how to use LogView and a case study on a real-life event log, please refer to the examples in our directory [notebooks](https://github.com/blindreview-logview123/logview/tree/main/notebooks)


<!-- CONTRIBUTING -->
## Contributing
If you have a suggestion that would make our project better, please let us know!
You can fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->
## License
Distributed under the GPL-3.0 License. See `LICENSE.txt` for more information.
