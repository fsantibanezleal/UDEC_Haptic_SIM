//---------------------------------------------------------------------------

#ifndef OpenHijaH
#define OpenHijaH
//---------------------------------------------------------------------------
#include <windows.h>
#include <stdio.h>
#include <math.h>

#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#pragma comment(lib, "glaux.lib")


#include <GL/gl.h>
#include <GL/glu.h>
#include <gl\glaux.h>
//---------------------------------------------------------------------------
public ref class TOpGl
{
	public:
		HDC hdc;
		HGLRC hrc;
	public:
		//__fastcall TOpGl(TComponent* Owner);
		//void  VentanaCreate(TObject *Sender);
		//void  VentanaDestroy(TObject *Sender);
		//void  VentanaPaint(TObject *Sender);
		//void  VentanaResize(TObject *Sender);
		//void  FormClose(TObject *Sender, TCloseAction &Action);
		//void  FormShow(TObject *Sender);
		//void SetCurrentWindow();		
};
//---------------------------------------------------------------------------
#endif
