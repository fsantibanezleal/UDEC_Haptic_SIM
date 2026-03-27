#ifndef OctreesH
#define OctreesH

#include "Cuerpo.h"

typedef struct Octrees
{
	//int		opcion de dar mas hijos
	bool	raiz;
	bool	descendencia;
	bool	*cuerposPresentes; // [numCuerposTotal] ::: cuerposPresentes[i]=true si en esta rama del octree se halla ese cuerpo .. largo de vRuta->numCuerpos

	int     recCuerposP; // numero de cuerpos presentes... no cuales son..como el bool superior *CuerposPresentes
	int		numPuntos; // Total de Puntos en Octree usado para evaluar division
	int		*numPartes; // Indica el numero de partes existentes en cada objeto en particular.. no usado todavia
	int		*nPoligonosPCuerpos; // poligonos por cada cuerpo largo de CuerposPresentes

	int		*PolListos;// Indica el numero de poligonos de cada cuerpo que estan en la rama y estan listos para direccionar al inferior
	int		**IndicePolSubOctree; // contiene los indices a poligonos por cada cuerpo en el octree [numCuerpos][nPoligonospCuerpos[cuerpoParticular]]
		
	float	minMax[6]; // xMin,xMax,yMin,yMax,zMin,zMax
	float	medXYZ[3];

   	struct	Octrees	*hijos[8]; // 2^2^3 2^3n usualmente n=2(multiplos es lo mismo) seria interesante con tres....
	struct	Octrees	*Padre;
}Octree;
typedef	Octree	*PunteroBloque;
typedef	Octree	*Bloque;

struct RutaPuntos
{
	int				numPuntosT,numCuerpos;
	
	bool			factorC;				// Indica si NO debe dividir al hallar un bloque igual al padre en numero de puntos..
	int				factorU;			// Numero minimo de puntos para triangulo....
	float			factorG,factorR;    // G numero puntos porcentaje minimo para la division;; R dimension minima de division en relacion al ancho del octree principal
	
	PunteroBloque	*octreeAnteriorActual; // largo 2*numPuntos 2*i+0 es anterior y 2*i+1 el actual
};

bool	CrearRuta(RutaPuntos *vRuta,Cuerpo *vCuerpo,int vElementos);

Bloque	CrearBloque(float vLimites[6]);
void	InsertarSubBloques(PunteroBloque vPB,int vNumCuerpos); 
bool	BorrarSubBloquesOctree(PunteroBloque vPB,int vNumCuerpos);
void	DestruirBloque(Bloque vBloque, int vNumCuerpos);

bool	DesarrollarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,int vElementos,float vDXYZ[3],int vHaptico);
bool	DesarrollarHijos(Bloque vSubOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,float vDXYZ[3],int vHaptico);

bool	ColisionarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,int vHaptico);
bool	ActualizarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo);
bool	DibujarOctree(Bloque vOctree);
bool	DibujarBloque(Bloque vBloque);

#endif