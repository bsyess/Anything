#include<iostream>
using namespace std;
int print(int*a,int n,int k,int x)
{
	int i=x,j=x;
	for(i=x;i<n-1-x;i++)
	{
		a[i*n+j]=k;
		k++;
	}
	x++;
	if(x==n-x)
	{
		return 0;
	}
	for(j=x;j<n-1-x;j++)
	{
		a[i*n+j]=k;
		k++;
	}
	for(;i>=x;i--)
	{
		a[i*n+j]=k;
		k++;
	}
	x++;
	if(x==n-x)
	{
		return 0;
	}
	for(;j>=x+1;j--)
	{
		a[i*n+j]=k;
		k++;
	}
	return print(a,n,k,x);
}
int main()
{
	int n,k=1;
	int x=0;
	cin>>n;
	int a[n*n];
	print(a,n,k,x);
	for(k=0;k<n;k++)
	{
		for(x=0;x<n;x++)
		{
			cout<<a[k*n+x]<<' ';
		}
		cout<<endl;
	}
	return 0;
}
