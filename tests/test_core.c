#include "../Filter_Core/Filter_Core.h"
#include <stdint.h>
#include <stdio.h>

int32_t ax;
int32_t az;
ma_t Qx;
ma_t Qz;

int main(){
    ma_init(&Qx);
    ma_init(&Qz);
    while(scanf("%d,%d\n", &ax, &az) == 2){
     
     int32_t fx = ma_update( &Qx,  ax);
     int32_t fz = ma_update( &Qz,  az);

     int32_t fpitch = pitch_cdeg(fx,fz);
     int32_t pitch = pitch_cdeg(ax,az);
     printf("%d,%d,%d,%d,%d,%d\n",ax,az,fx,fz,pitch,fpitch);
     
    }
       return 0;
}
