#include"guess.h"
#include <map>
#include <string>
#include <cstring>
#include <cstdlib>
#include <assert.h>
#include <iostream>
#define set0(x) memset(x,0,sizeof(x))
using namespace std;
int qz[1010],qued[1010][1010],vis[1010][1010];
char ooo[4040],*ocr = ooo+2000;
int que(int l,int r){
	if(vis[l][r])return qued[l][r];
	vis[l][r] = 1;
	return qued[l][r] = query(l-1,r-1);
}
string guess(){
	srand(4100625);
	set0(qued);
	set0(vis);
	set0(ooo);
	ocr[que(1,1000)]++;
	for(int i=1;i<=999;i++){
		int c = que(1,i)+que(i+1,1000);
		ocr[c]++;
		if(ocr[c]>=50){
			qz[1000] = c;
			break;
		}
	}
	string S;
	for(int i=1;i<=50;i++){
		set0(ooo);
		ocr[qz[1000]-que(i+1,1000)]++;
		for(int j=500;j<600;j++){
			int cc = qz[1000]-que(i+1,j)-que(j+1,1000);
			ocr[cc]++;
			if(ocr[cc]>=4 && cc>=qz[i-1] && cc<=qz[i-1]+1){
				qz[i] = cc;
				break;
			}
		}
	}
	for(int i=999;i>=950;i--){
		set0(ooo);
		for(int j=1;j<50;j++){
			int cc = que(j+1,i)+qz[j];
			ocr[cc]++;
			if(ocr[cc]>=4 && cc<=qz[i+1] && cc>=qz[i+1]-1){
				qz[i] = cc;
				break;
			}
		}
	}
	for(int i=51;i<=500;i++){
		set0(ooo);
		for(int j=1000;j>=950;j--){
			int cc =qz[j]-que(i+1,j);
			ocr[cc]++;
			if(ocr[cc]>=2 && cc>=qz[i-1] && cc<=qz[i-1]+1){
				qz[i] = cc;
				break;
			}
		}
	}
	for(int i=501;i<=950;i++){
		set0(ooo);
		for(int j=0;j<50;j++){
			int cc =qz[j]+que(j+1,i);
			ocr[cc]++;
			if(ocr[cc]>=2 && cc>=qz[i-1] && cc<=qz[i-1]+1){
				qz[i] = cc;
				break;
			}
		}
	}
	for(int i=1;i<=1000;i++)S+='0'+qz[i]-qz[i-1];
	return S;
}
