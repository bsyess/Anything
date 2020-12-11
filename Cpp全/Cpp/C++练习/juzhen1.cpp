#include<iostream>
using namespace std;
class Matrix
{
	public:
		int a[10][10],n;
		Matrix(){};
};

istream & operator >>(istream &in,Matrix &m)
		{
			int i,j;
			in>>m.n;
			for(i=0;i<m.n;i++)
			{
				for(j=0;j<m.n;j++)
				{
					in>>m.a[i][j];
				}
			}
			return in;
		}
		ostream & operator <<(ostream & out,Matrix &m)
		{
			int i,j;
			
			for(i=0;i<m.n;i++)
			{
				for(j=0;j<m.n;j++)
				{
					out<<m.a[i][j];
					cout<<' ';
				}
				cout<<endl;
			}
			return out;
		}
		Matrix operator * (Matrix m1,Matrix m2)
		{
			int f[100];
			Matrix m3;
			m3.n=m1.n;
			int i,j,k,sum=0;
			for(i=0;i<m1.n;i++)
			{
				for(j=0;j<m1.n;j++)
				{
					sum=0;
					for(k=0;k<m1.n;k++)
					{
						sum=sum+m1.a[i][k]*m2.a[k][j];
					}
					m3.a[i][j]=sum;
				}
			}
			return m3;
			
		}
int main()
{
	Matrix m1,m2,m3;
	cin>>m1;
	cin>>m2;
	m3=m1*m2;
	cout<<m1;
	cout<<m2;
	cout<<m3;
	return 0;
}
