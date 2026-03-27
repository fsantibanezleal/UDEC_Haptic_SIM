#ifndef float3
typedef struct { 
	float x;
	float y;
	float z;
} float3;
#endif

#ifndef float4
typedef struct { 
	float x;
	float y;
	float z;
	float w;
} float4;
#endif

#ifndef uint3
typedef struct { 
	unsigned x;
	unsigned y;
	unsigned z;
} uint3;
#endif

#ifndef uint4
typedef struct { 
	unsigned x;
	unsigned y;
	unsigned z;
	unsigned w;
} uint4;

//float ppunto4( float * a,float * b) { 
//	float r= 0 ;
//    for (unsigned i =0;i<4;i++)		r+=a[i]*b[i];
//	return r;
//} 
//void algo(float4 a, float4 b)
//{   
//  suma4(&(a.x),&(b.x));
//  float e[4];
//  float4 * b;
//   b = (float4 *)e;
//
//}
//
//float ppunto( float4 const & va,float4 const & vb) { 
//	float r= 0 ;
//	float  * a=&va.x;
//	float *  b=&vb.y;
//    for (unsigned i =0;i<4;i++)		r+=a[i]*b[i];
//	va.x=1;
//	return r;
//} 
//
//float ppunto( float3 & va,float3 & vb) { 
//	float r= 0 ;
//	float  * a=&va.x;
//	float *  b=&vb.y;
//    for (unsigned i =0;i<3;i++)		r+=a[i]*b[i];
//	return r;
//} 