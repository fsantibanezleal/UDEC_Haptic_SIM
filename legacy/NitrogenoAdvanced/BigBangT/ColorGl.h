//****Para tratar vColor como vector y emplear vColor para setear vColores

#ifndef ColorGlH
#define ColorGlH

#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#pragma comment(lib, "glaux.lib")


#include <GL/gl.h>
#include <GL/glu.h>
#include <gl\glaux.h>

using namespace System::Drawing;

const GLint mRed=256;
const GLint mGreen=65536;
const GLint mBlue=mRed*mGreen;
const GLint mAlfa=(int)((double)mGreen*(double)mGreen);

class ColorGl
{
	private:
		GLdouble rojo,verde,azul,alfa,intensidad;
	public:
		ColorGl()
		{
			rojo =verde=azul= 0;
			alfa =intensidad= 1;
		};
		ColorGl(GLdouble vRojo,GLdouble vVerde,GLdouble vAzul)
		{
			rojo = vRojo;
			verde= vVerde;
			azul = vAzul;
			alfa =intensidad= 1;
		};

		ColorGl(GLdouble vRojo,GLdouble vVerde,GLdouble vAzul,GLdouble vAlfa)
		{
			rojo = vRojo;
			verde= vVerde;
			azul = vAzul;
			alfa = vAlfa;
			intensidad= 1;
		};

		void SetColorGl(GLdouble vRojo,GLdouble vVerde,GLdouble vAzul)
		{
			rojo = vRojo;
			verde= vVerde;
			azul = vAzul;
		};

		void SetColorGl(GLdouble vRojo,GLdouble vVerde,GLdouble vAzul, GLdouble vAlpha)
		{
			rojo = vRojo;
			verde= vVerde;
			azul = vAzul;
			alfa = vAlpha;
		};

		void	 Red(GLdouble vRojo){rojo=vRojo;};
		GLdouble Red(){return rojo;};
		void	 Green(GLdouble vVerde){verde=vVerde;};
		GLdouble Green(){return verde;};
		void	 Blue(GLdouble vAzul){azul=vAzul;};
		GLdouble Blue(){return azul;};
		void	 Alpha(GLdouble vAlfa){alfa=vAlfa;};
		GLdouble Alpha(){return alfa;};
		void	 I(GLdouble vIntensidad){intensidad=vIntensidad;};
		GLdouble I(){return intensidad;};

		ColorGl ToColorGl(Color vColor)
		{
			GLint vRojo,vVerde,vAzul,vAlfa,normal;
			normal=abs(vColor.ToArgb());
			normal=normal-mAlfa*((GLint) (normal/mAlfa));
			vAlfa=(GLint)(normal/mBlue); // Entre 0 y 256
			normal=normal-vAlfa*mBlue;
			vAzul =(GLint)(normal/mGreen);
			normal= normal-vAzul*mGreen;
			vVerde= (GLint)(normal/mRed);
			vRojo= normal - vVerde*mRed;

			vAlfa=vAlfa<0? 0:vAlfa;
			vRojo=vRojo<0? 0:vRojo;
			vVerde=vVerde<0? 0:vVerde;
			vAzul=vAzul<0? 0:vAzul;

			vAlfa=vAlfa>256? 256:vAlfa;
			vRojo=vRojo>256? 256:vRojo;
			vVerde=vVerde>256? 256:vVerde;
			vAzul=vAzul>256? 256:vAzul;

			return ColorGl((double)vRojo/256.0,(double)vVerde/256.0,(double)vAzul/256.0,(double)vAlfa/256.0);
		};

		void ToColorGlChange(Color vColor)
		{
			GLdouble normal;
			normal=abs(vColor.ToArgb());
			normal=normal-mAlfa*((GLint)(normal/mAlfa));
			alfa=normal/mBlue; // Entre 0 y 256
			normal=normal-alfa*mBlue;
			azul =normal/mGreen;
			normal= normal-azul*mGreen;
			verde= normal/mRed;
			rojo= normal - verde*mRed;

			alfa=alfa<0? 0.0:(double)alfa/256.0;
			rojo=rojo<0? 0.0:(double)rojo/256.0;
			verde=verde<0? 0.0:(double)verde/256.0;
			azul=azul<0? 0.0:(double)azul/256.0;

			alfa=alfa>1.0? 1.0:(double)alfa;
			rojo=rojo>1.0? 1.0:(double)rojo;
			verde=verde>1.0? 1.0:(double)verde;
			azul=azul>1.0? 1.0:(double)azul;
		};

		Color ToColor(ColorGl vColor)
		{
			return( Color::FromArgb((int)((double)mAlfa*vColor.alfa+(double)mBlue*vColor.azul+(double)mGreen*vColor.verde+(double)mRed*vColor.rojo)));
		};

		inline friend ColorGl operator+ ( const ColorGl V1, const ColorGl V2)
		{
			GLdouble vRojo,vVerde,vAzul,vAlfa;

			vRojo=  V1.rojo+V2.rojo;
			vVerde= V1.verde+V2.verde;
			vAzul=  V1.azul+V2.azul;
			vAlfa=  V1.alfa+V2.alfa;

			vAlfa=vAlfa<0.0? 0.0:(double)vAlfa;
			vRojo=vRojo<0.0? 0.0:(double)vRojo;
			vVerde=vVerde<0.0? 0.0:(double)vVerde;
			vAzul=vAzul<0.0? 0.0:(double)vAzul;

			vAlfa=vAlfa>1.0? 1.0:(double)vAlfa;
			vRojo=vRojo>1.0? 1.0:(double)vRojo;
			vVerde=vVerde>1.0? 1.0:(double)vVerde;
			vAzul=vAzul>1.0? 1.0:(double)vAzul;

			return ColorGl(vRojo,vVerde,vAzul,vAlfa);
		};

		inline friend ColorGl operator* ( const GLdouble V1, const ColorGl V2)
		{
			return ColorGl(V1*V2.rojo,V1*V2.verde,V1*V2.azul);
		};
};
#endif