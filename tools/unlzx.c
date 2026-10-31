#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mspack.h"
#include "system.h"
#include "lzx.h"
struct mem { unsigned char *buf; size_t len, pos; };
static struct mem in, out;
static struct mspack_file *mopen(struct mspack_system *s, const char *f, int m){ return (struct mspack_file*)(f[0]=='i'?&in:&out);}
static void mclose(struct mspack_file *f){}
static int mread(struct mspack_file *f, void *b, int n){ struct mem*m=(struct mem*)f; size_t r=m->len-m->pos; if(r>(size_t)n) r=n; memcpy(b,m->buf+m->pos,r); m->pos+=r; return (int)r;}
static int mwrite(struct mspack_file *f, void *b, int n){ struct mem*m=(struct mem*)f; if(m->pos+n>m->len) n=m->len-m->pos; memcpy(m->buf+m->pos,b,n); m->pos+=n; return n;}
static int mseek(struct mspack_file *f, off_t o, int mode){return 0;}
static off_t mtell(struct mspack_file *f){return ((struct mem*)f)->pos;}
static void mmsg(struct mspack_file *f, const char *fmt, ...){}
static void *malloc_(struct mspack_system *s, size_t n){return malloc(n);}
static void free_(void *p){free(p);}
static void copy_(void *a, void *b, size_t n){memmove(b,a,n);}
int main(int c, char**v){
  FILE*f=fopen(v[1],"rb"); fseek(f,0,2); in.len=ftell(f); fseek(f,0,0); in.buf=malloc(in.len); fread(in.buf,1,in.len,f); fclose(f);
  out.len=strtoul(v[3],0,0); out.buf=calloc(1,out.len);
  int wbits=atoi(v[4]);
  struct mspack_system sys={mopen,mclose,mread,mwrite,mseek,mtell,mmsg,malloc_,free_,copy_,NULL};
  struct lzxd_stream *s=lzxd_init(&sys,(struct mspack_file*)&in,(struct mspack_file*)&out,wbits,0,0x8000,out.len,0);
  int r=lzxd_decompress(s,out.len);
  fprintf(stderr,"lzxd result %d, wrote %zu\n",r,out.pos);
  f=fopen(v[2],"wb"); fwrite(out.buf,1,(r?s->offset:out.len),f); fclose(f);
  return r;
}
