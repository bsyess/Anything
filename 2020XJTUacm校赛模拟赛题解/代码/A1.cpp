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

int ax,ay,bx,by,cx,cy;

int main()
{
	cin>>ax>>ay>>bx>>by>>cx>>cy;
	DB ans=LLINF;
	int x,y;
	for (int i=-1000;i<=1000;i++)
		for (int j=-1000;j<=1000;j++)
		{
			double da=sqrt((ax-i)*(ax-i)+(ay-j)*(ay-j));
			double db=sqrt((bx-i)*(bx-i)+(by-j)*(by-j));
			double dc=sqrt((cx-i)*(cx-i)+(cy-j)*(cy-j));
			double d=3*da+2*db+dc;
			if (d<ans)
			{
				ans=d;
				x=i;
				y=j;
			}
		}
	cout<<x<<' '<<y<<endl;
	return ~~(0^_^0);
}
