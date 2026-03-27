// stdafx.h : include file for standard system include files,
// or project specific include files that are used frequently, but
// are changed infrequently
#pragma once

#include <windows.h>
#include <stdio.h>
#include <math.h>
#include <assert.h>
#using <mscorlib.dll>

#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#pragma comment(lib, "glaux.lib")


#include <GL/gl.h>
#include <GL/glu.h>
#include <gl\glaux.h>

#include <HD/hd.h>
#include <HDU/hdu.h>
#include <HDU/hduError.h>
#include <HDU/hduVector.h>



// TODO: reference additional headers your program requires here

using namespace System;
using namespace System::Drawing;
using namespace System::IO;
using namespace System::Windows::Forms;
using namespace System::Globalization;

#define CURSOR_SIZE_PIXELS 20