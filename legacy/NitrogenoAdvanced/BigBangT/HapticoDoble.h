#ifndef HapticoDobleH
#define	HapticoDobleH

#include <assert.h>

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
#include <HDU/hduMatrix.h>

#define CURSOR_SIZE_PIXELS 20

typedef struct
{
    HDboolean		isAnchorActive;
	HDfloat			transform[16];
	hduVector3Df	position;
    hduVector3Df	anchor;
} HapticDisplayState;

class HapticoDoble
{
	public:
		bool		creacion[2];

		bool		activo[2],habilitado[2];
		float		transformacion[2][16],posicion[2][3],pivote[2][3];
		double		kCursorScreenSize[2];
		double		gCursorScale[2];

		GLuint		gCursorDisplayList[2];
		HDdouble	workspacemodel[2][16];

		HDSchedulerHandle hUpdateDeviceCallback;

	public:
		HapticoDoble();
		
		~HapticoDoble();
	public:
		int exitHandler(void);

		void Actualizar();
		void drawAnchor(const HapticDisplayState *pState);
		void updateWorkspace();
};
#endif