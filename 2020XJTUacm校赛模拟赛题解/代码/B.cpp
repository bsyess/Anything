#include <bits/stdc++.h>
#define DB double
#define LL long long

#define MST(a,b) memset((a),(b),sizeof(a))
#define MRK() cout<<"Mark"<<endl;
#define WRT(x) cout<<#x<<" = "<<(x)<<endl;

#define MAXN 210000
#define MAXM 410000
#define MOD 998244353
#define INF 0x3f3f3f3f
#define LLINF 0x3f3f3f3f3f3f3f3f
#define EPS 1e-5

#define _ 0
using namespace std;

DB h,m;
DB ph,pm;

int main()
{
	scanf("%lf:%lf",&h,&m);
	if (h>=12)
		h-=12;
	ph=(h/12*360+m/60*30);
	pm=m/60*360;
	DB p=fabs(ph-pm);
	if (p>180)
		p=360-p;
	printf("%.1lf",p); 
	return ~~(0^_^0);
}
