/*
Copyright (c) 2008, Yahoo! Inc. All rights reserved.
Code licensed under the BSD License:
http://developer.yahoo.net/yui/license.txt
version: 3.0.0pr2
*/
YUI.add("cookie",function(B){var J=B.Lang,H=B.Object,F=null,C=J.isString,K=J.isObject,E=J.isUndefined,D=J.isFunction,G=encodeURIComponent,A=decodeURIComponent;function I(L){throw new TypeError(L);}B.Cookie={_createCookieString:function(M,O,N,L){var P=G(M)+"="+(N?G(O):O);if(K(L)){if(L.expires instanceof Date){P+="; expires="+L.expires.toGMTString();}if(C(L.path)&&L.path!==""){P+="; path="+L.path;}if(C(L.domain)&&L.domain!==""){P+="; domain="+L.domain;}if(L.secure===true){P+="; secure";}}return P;},_createCookieHashString:function(L){if(!K(L)){I("Cookie._createCookieHashString(): Argument must be an object.");}var M=[];H.each(L,function(O,N){if(!D(O)&&!E(O)){M.push(G(N)+"="+G(String(O)));}});return M.join("&");},_parseCookieHash:function(P){var O=P.split("&"),Q=F,N={};if(P.length){for(var M=0,L=O.length;M<L;M++){Q=O[M].split("=");N[A(Q[0])]=A(Q[1]);}}return N;},_parseCookieString:function(S,U){var T={};if(C(S)&&S.length>0){var L=(U===false?function(V){return V;}:A);if(/[^=]+=[^=;]?(?:; [^=]+=[^=]?)?/.test(S)){var Q=S.split(/;\s/g),R=F,M=F,O=F;for(var N=0,P=Q.length;N<P;N++){O=Q[N].match(/([^=]+)=/i);if(O instanceof Array){R=A(O[1]);M=L(Q[N].substring(O[1].length+1));}else{R=A(Q[N]);M=R;}T[R]=M;}}}return T;},get:function(L,M){var N=this._parseCookieString(document.cookie);if(!C(L)||L===""){I("Cookie.get(): Cookie name must be a non-empty string.");}if(E(N[L])){return F;}if(!D(M)){return N[L];}else{return M(N[L]);}},getSub:function(L,N,M){var O=this.getSubs(L);if(O!==F){if(!C(N)||N===""){I("Cookie.getSub(): Subcookie name must be a non-empty string.");}if(E(O[N])){return F;}if(!D(M)){return O[N];}else{return M(O[N]);}}else{return F;}},getSubs:function(L){if(!C(L)||L===""){I("Cookie.getSubs(): Cookie name must be a non-empty string.");}var M=this._parseCookieString(document.cookie,false);if(C(M[L])){return this._parseCookieHash(M[L]);}return F;},remove:function(M,L){if(!C(M)||M===""){I("Cookie.remove(): Cookie name must be a non-empty string.");}L=L||{};L.expires=new Date(0);return this.set(M,"",L);},removeSub:function(M,O,L){if(!C(M)||M===""){I("Cookie.removeSub(): Cookie name must be a non-empty string.");}if(!C(O)||O===""){I("Cookie.removeSub(): Subcookie name must be a non-empty string.");}var N=this.getSubs(M);if(K(N)&&H.owns(N,O)){delete N[O];return this.setSubs(M,N,L);}else{return"";}},set:function(M,N,L){if(!C(M)){I("Cookie.set(): Cookie name must be a string.");}if(E(N)){I("Cookie.set(): Value cannot be undefined.");}var O=this._createCookieString(M,N,true,L);document.cookie=O;return O;},setSub:function(M,O,N,L){if(!C(M)||M===""){I("Cookie.setSub(): Cookie name must be a non-empty string.");}if(!C(O)||O===""){I("Cookie.setSub(): Subcookie name must be a non-empty string.");}if(E(N)){I("Cookie.setSub(): Subcookie value cannot be undefined.");}var P=this.getSubs(M);if(!K(P)){P={};}P[O]=N;return this.setSubs(M,P,L);},setSubs:function(M,N,L){if(!C(M)){I("Cookie.setSubs(): Cookie name must be a string.");}if(!K(N)){I("Cookie.setSubs(): Cookie value must be an object.");}var O=this._createCookieString(M,this._createCookieHashString(N),false,L);document.cookie=O;return O;}};},"3.0.0");