//---------------------------------------------------------------------------

#pragma hdrstop

#include "OpenHija.h"

//void TOpGl::VentanaCreate()
//{
//	int PixelFormat;
//	hdc= GetDC(OpGl->Handle);
//	PIXELFORMATDESCRIPTOR pfd=
//	{
//			sizeof(PIXELFORMATDESCRIPTOR),
//			1,
//			PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER ,
//			PFD_TYPE_RGBA,
//			32,
//			0,0,0,0,0,0,
//			  0,0,
//			  0,0,0,0,0,
//			32,
//			0,
//			0,
//			PFD_MAIN_PLANE,
//			0,
//			0,0,
//
//	};
//	PixelFormat = ChoosePixelFormat(hdc,&pfd);
//	SetPixelFormat(hdc, PixelFormat, &pfd);
//	hrc = wglCreateContext(hdc);
//	if(hrc == NULL)
//	{
//		Application->MessageBox(
//			"0 No se puede inicialzar OpenGL",
//			"ERROR",
//			MB_OK | MB_ICONERROR);
//		Application->Terminate();
//	}
//	if(wglMakeCurrent(hdc,hrc)==false)
//	{
//		Application->MessageBox(
//			"1 No se´puede inicializar OpenGL",
//			"ERROR",
//			MB_OK | MB_ICONERROR);
//		Application->Terminate();
//	}
//}
//
//void TOpGl::SetCurrentWindow()
//{
//	if( wglMakeCurrent(hdc,hrc) == false)
//	{
//		Application->MessageBox(
//		"2 No se puede inicializar OpenGL",
//		"ERROR Externa",
//		MB_OK	| MB_ICONERROR );
//		Application->Terminate();
//	}
//}
//
//void __fastcall TOpGl::VentanaDestroy(TObject *Sender)
//{
//	wglMakeCurrent (NULL, NULL) ;
//	wglDeleteContext(hrc);
//}
//
//void __fastcall TOpGl::VentanaPaint(TObject *Sender)
//{
//	FormPadre->VentanaPaint(Sender);
//}
//
//void __fastcall TOpGl::VentanaResize(TObject *Sender)
//{
//	FormPadre->FormResize(Sender);
//}
//
//void __fastcall TOpGl::FormClose(TObject *Sender, TCloseAction &Action)
//{
//  	FormPadre->Retorno();
//}
////---------------------------------------------------------------------------
//
//void __fastcall TOpGl::FormShow(TObject *Sender)
//{
//	SetCurrentWindow();
//}
////---------------------------------------------------------------------------
//
