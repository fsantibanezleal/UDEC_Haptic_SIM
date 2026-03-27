//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include <windows.h>

#include "OpenForPanel.h"


using namespace System;
using namespace System::Drawing;
using namespace System::IO;
using namespace System::Windows::Forms;

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

void TOpenGl::VentanaCreate(HWND MyHwnd)
{
	int PixelFormat;
	this->hdc= GetDC(MyHwnd);
	PIXELFORMATDESCRIPTOR pfd=
	{
			sizeof(PIXELFORMATDESCRIPTOR),
			1,
			PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER ,
			PFD_TYPE_RGBA,
			32,
			0,0,0,0,0,0,
			  0,0,
			  0,0,0,0,0,
			32,
			0,
			0,
			PFD_MAIN_PLANE,
			0,
			0,0,

	};
	PixelFormat = ChoosePixelFormat(this->hdc,&pfd);
	SetPixelFormat(this->hdc, PixelFormat, &pfd);
	this->hrc = wglCreateContext(this->hdc);
	if(this->hrc == NULL)
	{
		MessageBox::Show("wglCreateContext Failed");
	}
	if(wglMakeCurrent(this->hdc,this->hrc)==false)
	{
		MessageBox::Show("wglMakeCurrent Failed");
	}
}

void TOpenGl::VentanaCreate2(HWND MyHwnd)
{
	int PixelFormat;
	this->hdc2= GetDC(MyHwnd);
	PIXELFORMATDESCRIPTOR pfd=
	{
			sizeof(PIXELFORMATDESCRIPTOR),
			1,
			PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER ,
			PFD_TYPE_RGBA,
			32,
			0,0,0,0,0,0,
			  0,0,
			  0,0,0,0,0,
			32,
			0,
			0,
			PFD_MAIN_PLANE,
			0,
			0,0,

	};
	PixelFormat = ChoosePixelFormat(this->hdc2,&pfd);
	SetPixelFormat(this->hdc2, PixelFormat, &pfd);
	this->hrc2 = wglCreateContext(this->hdc2);
	if(this->hrc2 == NULL)
	{
		MessageBox::Show("wglCreateContext Failed");
	}
	if(wglMakeCurrent(this->hdc2,this->hrc2)==false)
	{
		MessageBox::Show("wglMakeCurrent Failed");
	}
}

void TOpenGl::VentanaDestroy()
{
	wglMakeCurrent (NULL, NULL) ;
	wglDeleteContext(this->hrc);
}

bool TOpenGl::SetCurrentWindow()
{
	if( wglMakeCurrent(this->hdc,this->hrc) == false)
	{
		MessageBox::Show("wglMakeCurrent Failed");
		return false;
	}
	return true;
}

bool TOpenGl::SetCurrentWindow2()
{
	if( wglMakeCurrent(this->hdc2,this->hrc2) == false)
	{
		MessageBox::Show("wglMakeCurrent2 Failed");
		return false;
	}
	return true;
}

