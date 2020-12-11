#include <bits/stdc++.h>
#define DB double
#define LL long long

#define MST(a,b) memset((a),(b),sizeof(a))
#define MRK() cout<<"Mark"<<endl;
#define WRT(x) cout<<#x<<" = "<<(x)<<endl;

#define MAXN 5010
#define MAXM 410000
#define MOD 998244353
#define INF 0x3f3f3f3f
#define LLINF 0x3f3f3f3f3f3f3f3f
#define EPS 1e-5

#define _ 0
using namespace std;

vector<int> g[MAXN]; 
int pool[MAXN][MAXN<<1];
int *dp[MAXN];
int n;
int col[MAXN],size[MAXN];

void init()
{
	int x,y;
	cin>>n;
	for (int i=1;i<n;i++)
	{
		scanf("%d%d",&x,&y);
		g[x].push_back(y);
		g[y].push_back(x);
	}
	for (int i=1;i<=n;i++)
		dp[i]=pool[i]+MAXN;
	col[1]=-1;
}

void dfs(int pos,int f)
{
	col[pos]=-col[f];
	for (auto p:g[pos])
		if (p!=f)
		{
			dfs(p,pos);
			size[pos]+=size[p];
		}
}

void clear(int *p,int n)
{
	for (int i=-n;i<=n;i++)
		p[i]=-INF;
}

int tpool[MAXN<<1];
int *tmp=tpool+MAXN;

void work(int pos,int f)
{
	int mx=-INF;
	size[pos]=1;
	clear(dp[pos],size[pos]);
	dp[pos][col[pos]]=0;
	for (auto p:g[pos])
		if (p!=f)
		{
			work(p,pos);
			clear(tmp,size[pos]+size[p]);
			for (int i=-size[pos];i<=size[pos];i++)
				for (int j=-size[p];j<=size[p];j++)
					tmp[i+j]=max(tmp[i+j],dp[pos][i]+dp[p][j]);
			size[pos]+=size[p];
			for (int i=-size[pos];i<=size[pos];i++)
				dp[pos][i]=tmp[i];
		}
	for (int i=-size[pos];i<=size[pos];i++)
		dp[pos][0]=max(dp[pos][0],dp[pos][i]+i*i);
}

int main()
{
	init();
	dfs(1,1);
	work(1,1); 
	cout<<(dp[1][0]-n);
	return ~~(0^_^0);
}
