# https://github.com/pygobject/pycairo/issues/59#issuecomment-316442034

import ctypes
import sys
import cairo  # pycairo
import cairocffi

from ctypes import c_void_p, py_object, c_char_p

class CAPI(ctypes.Structure):
    _fields_ = [
        ("Context_Type", py_object),
        ("Context_FromContext", ctypes.PYFUNCTYPE(py_object, c_void_p, py_object, py_object)),
    ]


def get_capi():
    if sys.version_info[0] == 2:
        PyCObject_AsVoidPtr = ctypes.PYFUNCTYPE(c_void_p, py_object)(
            ('PyCObject_AsVoidPtr', ctypes.pythonapi))
        ptr = PyCObject_AsVoidPtr(cairo.CAPI)
    else:
        PyCapsule_GetPointer = ctypes.PYFUNCTYPE(c_void_p, py_object, c_char_p)(
            ('PyCapsule_GetPointer', ctypes.pythonapi))
        ptr = PyCapsule_GetPointer(cairo.CAPI, b"cairo.CAPI")

    ptr = ctypes.cast(ptr, ctypes.POINTER(CAPI))
    return ptr.contents

def _UNSAFE_cairocffi_context_to_pycairo(cairocffi_context):  # noqa: N802
    # Sanity check. Continuing with another type would probably segfault.
    if not isinstance(cairocffi_context, cairocffi.Context):
        raise TypeError('Expected a cairocffi.Context, got %r'
                        % cairocffi_context)


    capi = get_capi()
    # Create a reference for PycairoContext_FromContext to take ownership of.

    ptr = cairocffi_context._pointer
    cairocffi.cairo.cairo_reference(ptr)

    ptr = int(cairocffi.ffi.cast('uintptr_t', ptr))
    return capi.Context_FromContext(ptr, capi.Context_Type, None)
