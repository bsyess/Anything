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

int getbitsum(int x)
{
	int sum=0;
	while (x)
	{
		sum+=x%10;
		x/=10;
	}
	return sum;
}

int buc[60];

int main()
{
	int n;
	cin>>n;
	for (int i=1;i<=n;i++)
		buc[getbitsum(i)]++;
	LL ans=0;
	for (int i=1;i<60;i++)
		ans+=buc[i]*buc[i];
	cout<<ans; 
	return ~~(0^_^0);
}
