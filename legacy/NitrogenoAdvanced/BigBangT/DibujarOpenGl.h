//---------------------------------------------------------------------------

#ifndef DibujarOpenGlH
#define DibujarOpenGlH

#include "OpenForPanel.h"
//#include "OpenHija.h"
#include "Cuerpo.h"
#include "Octrees.h"
#include "Haptico.h"

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

public ref class DibujarOpenGl
{
	public:
		GLboolean	rehacerDibujo,dibNormal,dibOctree,ProyPers;
		GLboolean 	swTestP,swModel,swFace,swOcul,swPStip;
		GLuint		swBackType,swFrontType,swPStipMask;
		GLuint		rendSelec,ilumSelec;
		GLuint		numObjetosAUsar,numObjetosEstablecidos;
		GLuint		indiceObjetoActivo,indiceObjetoHaptico,indiceObjetoHapticoAnt;

		GLfloat		*visualS,*visualR,*visualT,*limites;
		GLfloat		*DXYZ;
		
		GLdouble	*matrizT;

		ColorGl		*colorObjetos,*colorNormales;

		Poligono	*triangulos;
		Cuerpo		*Objetos;
		
		Bloque		octreePrincipal;		
		RutaPuntos	*octreeRuta;

		TOpenGl		Actuador;
	
		Haptico		*superHaptico;
		Haptico		*superHapticoApoyo;


	public:		// User declarations

		~DibujarOpenGl()
		{
			delete Objetos;
			delete colorNormales;
			delete colorObjetos;
			delete visualR;
			delete visualS;
			delete visualT;
			delete DXYZ;
			delete matrizT;
			delete octreeRuta->octreeAnteriorActual;
			delete octreeRuta;
		};

		void Inicializar();
		void Resize(int w, int h);

		void Selecciones();
		void Coordenadas();

		void LightP(GLint ilumSelec);
		void Renderizar(HDC hdcActual);
		void SelecRender(GLint rendSelec);

		void Dibujo1();
		void Dibujo2();
		void Dibujo3();
		void Dibujo4();
		void Dibujo5();
		void Dibujo6();				

		int SelecObjeto(GLuint vObjeto);
};
#endif
