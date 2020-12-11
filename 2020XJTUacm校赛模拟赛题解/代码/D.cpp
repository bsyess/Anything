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

int n,x;
int ans=0;

int main()
{
	cin>>n;
	while (n--)
	{
		scanf("%d",&x);
		ans^=x;
	}
	cout<<((ans&1) ? "ddd":"bqp")<<endl;
	return ~~(0^_^0);
}
