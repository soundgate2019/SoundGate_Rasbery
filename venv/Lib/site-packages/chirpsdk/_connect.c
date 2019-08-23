/* ------------------------------------------------------------------------
 *
 *  This file is part of the Chirp Connect Python SDK.
 *  For full information on usage and licensing, see https://chirp.io/
 *
 *  Copyright (c) 2011-2018, Asio Ltd.
 *  All rights reserved.
 *
 * ------------------------------------------------------------------------ */

#include <Python.h>
#include "include/chirp_connect_states.h"
#include "include/chirp_sdk_defines.h"

#if PY_MAJOR_VERSION >= 3
#define ERROR_INIT NULL
#else
#define ERROR_INIT /**/
#endif

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "_connect",
  NULL,
  -1,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL
};
#endif

PyMODINIT_FUNC
#if PY_MAJOR_VERSION >= 3
PyInit__connect(void)
#else
init_connect(void)
#endif
{
    PyObject* m;
    PyEval_InitThreads();

#if PY_MAJOR_VERSION >= 3
    m = PyModule_Create(&moduledef);
#else
    m = Py_InitModule("_connect", NULL);
#endif

    // Constants
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_NOT_CREATED);
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_STOPPED);
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_PAUSED);
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_RUNNING);
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_SENDING);
    PyModule_AddIntMacro(m, CHIRP_CONNECT_STATE_RECEIVING);
    PyModule_AddIntMacro(m, CHIRP_SDK_BUFFER_SIZE);

#if PY_MAJOR_VERSION >= 3
    return m;
#endif
}
