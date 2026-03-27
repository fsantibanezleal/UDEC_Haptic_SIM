//---------------------------------------------------------------------------

#ifndef OpenForPanelH
#define OpenForPanelH

#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#pragma comment(lib, "glaux.lib")


#include <GL/gl.h>
#include <GL/glu.h>
#include <gl\glaux.h>

//---------------------------------------------------------------------------
public ref class TOpenGl
{
	public:
		HDC hdc,hdc2;    				//Manipulador Ventana
		HGLRC hrc,hrc2;                  //Manipulador OpenGL

		TOpenGl(){};
		
		~TOpenGl()
		{
		};

		//TOpenGl(TOpenGl^ vTOp){hdc=vTOp->hdc;hrc=vTOp->hrc;};
		//TOpenGl^ operator=(TOpenGl^ vTOp){hdc=vTOp->hdc;hrc=vTOp->hrc;return this;};
		void VentanaCreate(HWND MyHwnd);
		void VentanaCreate2(HWND MyHwnd);
		bool SetCurrentWindow();
		bool SetCurrentWindow2();
		void VentanaDestroy();

	//private:	// User declarations
	public:		// User declarations
	
};

#endif