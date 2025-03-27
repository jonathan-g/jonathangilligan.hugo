library(reticulate)
library(rprojroot)

setwd(rprojroot::find_rstudio_root_file("bibliography"))

use_condaenv("r-reticulate")
for (module in c("yaml", "pybtex", "urllib")) {
  if (!py_module_available(module))
    py_install(module)
}
if (! py_module_available("dateutil")) {
  py_install("python-dateutil")
}

py_source("process_bibliography.py")
py_run_string("process('jgpubs.bib')")
