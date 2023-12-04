# cairocffi to pycairo conversion from
# https://github.com/Kozea/cairocffi/blob/master/utils/cairocffi_to_pycairo.py

# BSD 3-Clause License

# Copyright (c) 2013-2019, Simon Sapin and contributors.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import ctypes

import cairo  # pycairo
import cairocffi

pycairo = ctypes.PyDLL(cairo._cairo.__file__)
pycairo.PycairoContext_FromContext.restype = ctypes.c_void_p
pycairo.PycairoContext_FromContext.argtypes = 3 * [ctypes.c_void_p]
ctypes.pythonapi.PyList_Append.argtypes = 2 * [ctypes.c_void_p]


def _UNSAFE_cairocffi_context_to_pycairo(cairocffi_context):
    # Sanity check. Continuing with another type would probably segfault.
    if not isinstance(cairocffi_context, cairocffi.Context):
        raise TypeError('Expected a cairocffi.Context, got %r'
                        % cairocffi_context)

    # Create a reference for PycairoContext_FromContext to take ownership of.
    cairocffi.cairo.cairo_reference(cairocffi_context._pointer)
    # Casting the pointer to uintptr_t (the integer type as wide as a pointer)
    # gets the context’s integer address.
    # On CPython id(cairo.Context) gives the address to the Context type,
    # as expected by PycairoContext_FromContext.
    address = pycairo.PycairoContext_FromContext(
        int(cairocffi.ffi.cast('uintptr_t', cairocffi_context._pointer)),
        id(cairo.Context),
        None)
    assert address
    # This trick uses Python’s C API
    # to get a reference to a Python object from its address.
    temp_list = []
    assert ctypes.pythonapi.PyList_Append(id(temp_list), address) == 0
    return temp_list[0]
