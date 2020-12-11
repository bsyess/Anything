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

int n;
int x[MAXN],y[MAXN];
int ans=0;

int main()
{
	cin>>n;
	for (int i=0;i<n;i++)
	{
		scanf("%d%d",&x[i],&y[i]);
		if (x[i]>=0)
			ans|=1;
		if (x[i]<=0)
			ans|=2;
		if (y[i]>=0)
			ans|=4;
		if (y[i]<=0)
			ans|=8; 
	}
	if (ans==15)
		cout<<"banana"<<endl;
	else
		cout<<"ddd"<<endl;
	return ~~(0^_^0);
}
