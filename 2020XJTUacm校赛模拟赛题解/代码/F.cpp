#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

inline int gcd(int a, int b)
{
    return b ? gcd(b, a % b) : a;
}

inline int kpow(ll a, int k, int p)
{
    ll ans = 1;
    while (k)
    {
        if (k & 1)
            ans *= a, ans %= p;
        a *= a, a %= p;
        k >>= 1;
    }
    return ans;
}

int main()
{
        int k, p, n;
        vector<int> que;
        set<int> pop, ans;
        cin >> k >> p >> n;
        for (int i = 0; i < n; ++i)
        {
            int a;
            cin >> a;
            que.push_back(a);
        }
        for (int i = 1; i < p; ++i)
        {
            int ipk = kpow(i, k, p);
            if (gcd(ipk, p) == 1)
                pop.insert(ipk);
        }
        for (int i = 0; i < n; ++i)
            if (pop.count(que[i]))
                ans.insert(que[i]);
        cout << ans.size() << endl;
        for (int a : ans)
            cout << a << " ";
    return 0;
}
