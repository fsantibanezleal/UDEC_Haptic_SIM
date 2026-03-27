//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#ifndef CuerpoH
#define CuerpoH

//#include "GeoBasica.h"
#include "ColorGl.h"

struct Poligono
{
	bool		colision,n,t;
	int			numVertices;
	float		*vertices;
	float		*normales;
	float		*texturas;

	float		pivote[3];

	ColorGl		colorRGBA;
};

struct PoligonoReferido
{
	bool	colision;
	int		numVertices;
	int*	indiceVertices;
	int*	indiceNormales;
	int*	indiceTexturas;
	float	normales[3];
};

struct MalladoReferido
{
	bool				deseado;
	int					numCaras; // numero de caras por cada "g" subobjeto
	PoligonoReferido	*malla;
};


struct Cuerpo
{
	bool	existencia;
	bool	deseado;
	bool	normales;
	bool	texturas;
	
	int		numG;	// numero de partes del objeto.. por lo general una para el proyecto por que se definen los elementos separados
	int		numP;	// numero de puntos del objeto 
	int		numT;	// numero de puntos de textura
	int		numN;	// numero de normales.... para la generacion dinamica del arreglo que las contendra

	float   pivote[3],vXYZ[3];
	
	float	*verPuntos;			// vector de numero de puntos del objeto *3 las coordenadas se emplean de forma lineal en vectores unidimensionales
	float	*verNormales;
	float	*verTexturas;

	ColorGl	colorRGBA;
	MalladoReferido	*partes; // Dinamico por que depende del numero de partes... si es una es tan solo un elemento de mallado
};

void NormalP(PoligonoReferido *vPoligono,float vPuntoA[3],float vPuntoB[3],float vPuntoC[3]);
bool CuerpoCopiar(Cuerpo *vCuerpo,Cuerpo *vCuerpoOrigen,bool vCambio);
bool CuerpoDibujar(Cuerpo *vCuerpo,ColorGl *vColorM,bool vNormales,ColorGl *vColorN,bool vTexturas); // vModo: puntos, lineas, relleno
bool CuerpoActualizar(Cuerpo *vCuerpo,Cuerpo *vCuerpoOrigen,float vPosicion[3],float *vMatrizT); // vModo: puntos, lineas, relleno
bool CuerpoEscalar(Cuerpo *vCuerpo,float vEscala[3],float vPivote[3]);
bool CuerpoTrasladar(Cuerpo *vCuerpo,float vTrasX,float vTrasY,float vTrasZ);
bool CuerpoRotar(Cuerpo *vCuerpo,float vAngulo[3],float vPivote[3]);
#endif