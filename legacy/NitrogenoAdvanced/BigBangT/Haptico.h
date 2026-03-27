#ifndef HapticoH
#define	HapticoH

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

class Haptico
{
	public:
		bool	creacion;
		HDSchedulerHandle hUpdateDeviceCallback;

		/* Ttransform that maps the haptic device workspace to world
		   coordinates based on the current camera view. */
		HDdouble	workspacemodel[16];
		float		*transformacion,posicion[3];
		bool		activo,habilitado;

		double kCursorScreenSize;
		GLuint gCursorDisplayList;
		double gCursorScale;

	public:
		Haptico();
		
		~Haptico();
	public:
		int exitHandler(void);

		void Actualizar();
		void drawCursor(const HapticDisplayState *pState);
		void drawAnchor(const HapticDisplayState *pState);
		void updateWorkspace();
};
#endif