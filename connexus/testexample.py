import json
import httplib
import urllib

globals = {"server": "connexusssar.appspot.com","port":"80","headers": {"Content-type": "application/json", "Accept": "text/plain"},"userId": "amy_hindman@yahoo.com"}

conn = httplib.HTTPConnection(globals["server"],globals["port"])

def send_request(conn, url, req, printinput):
    if(printinput):
        #Don't print if upload image json, too big.
        print "json request:"
        print '%s' % json.dumps(req)
    else:
        print 'Skipping json input due to size.'
    conn.request("POST", url, json.dumps(req), globals["headers"])
    resp = conn.getresponse()
    print "status reason"
    print resp.status, resp.reason
    response = resp.read()
    try:
        jsonresp = json.loads(response)
        print '  %s' % jsonresp
        return jsonresp
    except:
        print 'No json: ' + str(response)

if __name__ == '__main__':
    #Create a new stream
    print('Testing create a good stream')
    CreateStreamServiceURL = '/CreateStream'
    CreateStream1JSON = {"streamname": "amytest", "coverurl": "www.test.com", "currentuser": "amy_hindman@yahoo.com", "subscribers": ["amy_hindman@yahoo.com", "aimers1975@gmail.com", "bob@hotmail.com"], "tags": ["#test"]}
    response = send_request(conn,CreateStreamServiceURL,CreateStream1JSON,True)
    assert response == {'errorcode': 0}
    
    print('Testing error case: Stream of same name')
    #Errorcase - create a stream with same name
    response = send_request(conn,CreateStreamServiceURL,CreateStream1JSON,True)
    assert response == {'errorcode': 1}
    
    print('Testing error case: Stream with no username')
    #Handle error case where no user name is sent
    CreateStream1JSON = {"streamname": "amytest2", "coverurl": "www.test.com", "currentuser": "", "subscribers": ["amy_hindman@yahoo.com", "aimers1975@gmail.com", "bob@hotmail.com"], "tags": ["#test"]}
    response = send_request(conn,CreateStreamServiceURL,CreateStream1JSON,True)
    assert response == {'errorcode': 2}
    
    print('Testing error case: Stream with no streamname')
    #TODO: This needs to failHandle error case where no streamname is sent
    CreateStream1JSON = {"streamname": "", "coverurl": "www.test.com", "currentuser": "amy_hindman@yahoo.com", "subscribers": ["amy_hindman@yahoo.com", "aimers1975@gmail.com", "bob@hotmail.com"], "tags": ["#test"]}
    response = send_request(conn,CreateStreamServiceURL,CreateStream1JSON,True)
    assert response == {'errorcode': 3}
    #Upload an image
    
    print('Testing uploading image to stream')
    UploadImageServiceURL = '/UploadImage'
    UploadImageJSON = {"uploadimage": "/9j/4AAQSkZJRgABAQEAYABgAAD/4QAiRXhpZgAATU0AKgAAAAgAAQESAAMAAAABAAEAAAAAAAD/\n/gAEKgD/4gv4SUNDX1BST0ZJTEUAAQEAAAvoAAAAAAIAAABtbnRyUkdCIFhZWiAH2QADABsAFQAk\nAB9hY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAA9tYAAQAAAADTLQAAAAAp+D3er/JV\nrnhC+uTKgzkNAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBkZXNjAAABRAAAAHliWFla\nAAABwAAAABRiVFJDAAAB1AAACAxkbWRkAAAJ4AAAAIhnWFlaAAAKaAAAABRnVFJDAAAB1AAACAxs\ndW1pAAAKfAAAABRtZWFzAAAKkAAAACRia3B0AAAKtAAAABRyWFlaAAAKyAAAABRyVFJDAAAB1AAA\nCAx0ZWNoAAAK3AAAAAx2dWVkAAAK6AAAAId3dHB0AAALcAAAABRjcHJ0AAALhAAAADdjaGFkAAAL\nvAAAACxkZXNjAAAAAAAAAB9zUkdCIElFQzYxOTY2LTItMSBibGFjayBzY2FsZWQAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAWFlaIAAAAAAAACSgAAAPhAAAts9jdXJ2AAAAAAAABAAAAAAFAAoADwAU\nABkAHgAjACgALQAyADcAOwBAAEUASgBPAFQAWQBeAGMAaABtAHIAdwB8AIEAhgCLAJAAlQCaAJ8A\npACpAK4AsgC3ALwAwQDGAMsA0ADVANsA4ADlAOsA8AD2APsBAQEHAQ0BEwEZAR8BJQErATIBOAE+\nAUUBTAFSAVkBYAFnAW4BdQF8AYMBiwGSAZoBoQGpAbEBuQHBAckB0QHZAeEB6QHyAfoCAwIMAhQC\nHQImAi8COAJBAksCVAJdAmcCcQJ6AoQCjgKYAqICrAK2AsECywLVAuAC6wL1AwADCwMWAyEDLQM4\nA0MDTwNaA2YDcgN+A4oDlgOiA64DugPHA9MD4APsA/kEBgQTBCAELQQ7BEgEVQRjBHEEfgSMBJoE\nqAS2BMQE0wThBPAE/gUNBRwFKwU6BUkFWAVnBXcFhgWWBaYFtQXFBdUF5QX2BgYGFgYnBjcGSAZZ\nBmoGewaMBp0GrwbABtEG4wb1BwcHGQcrBz0HTwdhB3QHhgeZB6wHvwfSB+UH+AgLCB8IMghGCFoI\nbgiCCJYIqgi+CNII5wj7CRAJJQk6CU8JZAl5CY8JpAm6Cc8J5Qn7ChEKJwo9ClQKagqBCpgKrgrF\nCtwK8wsLCyILOQtRC2kLgAuYC7ALyAvhC/kMEgwqDEMMXAx1DI4MpwzADNkM8w0NDSYNQA1aDXQN\njg2pDcMN3g34DhMOLg5JDmQOfw6bDrYO0g7uDwkPJQ9BD14Peg+WD7MPzw/sEAkQJhBDEGEQfhCb\nELkQ1xD1ERMRMRFPEW0RjBGqEckR6BIHEiYSRRJkEoQSoxLDEuMTAxMjE0MTYxODE6QTxRPlFAYU\nJxRJFGoUixStFM4U8BUSFTQVVhV4FZsVvRXgFgMWJhZJFmwWjxayFtYW+hcdF0EXZReJF64X0hf3\nGBsYQBhlGIoYrxjVGPoZIBlFGWsZkRm3Gd0aBBoqGlEadxqeGsUa7BsUGzsbYxuKG7Ib2hwCHCoc\nUhx7HKMczBz1HR4dRx1wHZkdwx3sHhYeQB5qHpQevh7pHxMfPh9pH5Qfvx/qIBUgQSBsIJggxCDw\nIRwhSCF1IaEhziH7IiciVSKCIq8i3SMKIzgjZiOUI8Ij8CQfJE0kfCSrJNolCSU4JWgllyXHJfcm\nJyZXJocmtyboJxgnSSd6J6sn3CgNKD8ocSiiKNQpBik4KWspnSnQKgIqNSpoKpsqzysCKzYraSud\nK9EsBSw5LG4soizXLQwtQS12Last4S4WLkwugi63Lu4vJC9aL5Evxy/+MDUwbDCkMNsxEjFKMYIx\nujHyMioyYzKbMtQzDTNGM38zuDPxNCs0ZTSeNNg1EzVNNYc1wjX9Njc2cjauNuk3JDdgN5w31zgU\nOFA4jDjIOQU5Qjl/Obw5+To2OnQ6sjrvOy07azuqO+g8JzxlPKQ84z0iPWE9oT3gPiA+YD6gPuA/\nIT9hP6I/4kAjQGRApkDnQSlBakGsQe5CMEJyQrVC90M6Q31DwEQDREdEikTORRJFVUWaRd5GIkZn\nRqtG8Ec1R3tHwEgFSEtIkUjXSR1JY0mpSfBKN0p9SsRLDEtTS5pL4kwqTHJMuk0CTUpNk03cTiVO\nbk63TwBPSU+TT91QJ1BxULtRBlFQUZtR5lIxUnxSx1MTU19TqlP2VEJUj1TbVShVdVXCVg9WXFap\nVvdXRFeSV+BYL1h9WMtZGllpWbhaB1pWWqZa9VtFW5Vb5Vw1XIZc1l0nXXhdyV4aXmxevV8PX2Ff\ns2AFYFdgqmD8YU9homH1YklinGLwY0Njl2PrZEBklGTpZT1lkmXnZj1mkmboZz1nk2fpaD9olmjs\naUNpmmnxakhqn2r3a09rp2v/bFdsr20IbWBtuW4SbmtuxG8eb3hv0XArcIZw4HE6cZVx8HJLcqZz\nAXNdc7h0FHRwdMx1KHWFdeF2Pnabdvh3VnezeBF4bnjMeSp5iXnnekZ6pXsEe2N7wnwhfIF84X1B\nfaF+AX5ifsJ/I3+Ef+WAR4CogQqBa4HNgjCCkoL0g1eDuoQdhICE44VHhauGDoZyhteHO4efiASI\naYjOiTOJmYn+imSKyoswi5aL/IxjjMqNMY2Yjf+OZo7OjzaPnpAGkG6Q1pE/kaiSEZJ6kuOTTZO2\nlCCUipT0lV+VyZY0lp+XCpd1l+CYTJi4mSSZkJn8mmia1ZtCm6+cHJyJnPedZJ3SnkCerp8dn4uf\n+qBpoNihR6G2oiailqMGo3aj5qRWpMelOKWpphqmi6b9p26n4KhSqMSpN6mpqhyqj6sCq3Wr6axc\nrNCtRK24ri2uoa8Wr4uwALB1sOqxYLHWskuywrM4s660JbSctRO1irYBtnm28Ldot+C4WbjRuUq5\nwro7urW7LrunvCG8m70VvY++Cr6Evv+/er/1wHDA7MFnwePCX8Lbw1jD1MRRxM7FS8XIxkbGw8dB\nx7/IPci8yTrJuco4yrfLNsu2zDXMtc01zbXONs62zzfPuNA50LrRPNG+0j/SwdNE08bUSdTL1U7V\n0dZV1tjXXNfg2GTY6Nls2fHadtr724DcBdyK3RDdlt4c3qLfKd+v4DbgveFE4cziU+Lb42Pj6+Rz\n5PzlhOYN5pbnH+ep6DLovOlG6dDqW+rl63Dr++yG7RHtnO4o7rTvQO/M8Fjw5fFy8f/yjPMZ86f0\nNPTC9VD13vZt9vv3ivgZ+Kj5OPnH+lf65/t3/Af8mP0p/br+S/7c/23//2Rlc2MAAAAAAAAALklF\nQyA2MTk2Ni0yLTEgRGVmYXVsdCBSR0IgQ29sb3VyIFNwYWNlIC0gc1JHQgAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAABYWVogAAAAAAAAYpkAALeFAAAY2lhZWiAAAAAAAAAAAABQAAAAAAAAbWVhcwAAAAAA\nAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACWFlaIAAAAAAAAAMWAAADMwAAAqRYWVogAAAAAAAA\nb6IAADj1AAADkHNpZyAAAAAAQ1JUIGRlc2MAAAAAAAAALVJlZmVyZW5jZSBWaWV3aW5nIENvbmRp\ndGlvbiBpbiBJRUMgNjE5NjYtMi0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABYWVogAAAAAAAA9tYA\nAQAAAADTLXRleHQAAAAAQ29weXJpZ2h0IEludGVybmF0aW9uYWwgQ29sb3IgQ29uc29ydGl1bSwg\nMjAwOQAAc2YzMgAAAAAAAQxEAAAF3///8yYAAAeUAAD9j///+6H///2iAAAD2wAAwHX/2wBDAAIB\nAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0M\nDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM\nDAwMDAwMDAwMDAwMDAwMDAz/wAARCACrAMADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAA\nAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEI\nI0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlq\nc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW\n19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL\n/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLR\nChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE\n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\nxy1scPLdn//Z\n", "streamname": "amytest", "contenttype": "image/jpeg", "comments": "This is my pic", "filename": "testpic.jpg"}
    response = send_request(conn,UploadImageServiceURL,UploadImageJSON,False)
    assert response == {'errorcode': 0}
    
    print('Testing viewing stream amytest')
    ViewStreamServiceURL = '/ViewStream'
    ViewStreamServiceJSON = {"pagerange": [0, 0], "streamname": "amytest"}
    response = send_request(conn,ViewStreamServiceURL,ViewStreamServiceJSON,True)
    assert response['pagerange'] == [0, 0]
    assert len(response['picurls']) == 1

    print('Testing manage streams returns proper streams')
    ManageStreamURL = '/ManageStream'
    ManageStreamJSON = {"userid":"amy_hindman@yahoo.com"}
    response = send_request(conn,ManageStreamURL,ManageStreamJSON,True)
    print('Streamlist is: ' + str(response['streamlist']) + '\n')
    print('Subscribed stream list is: ' + str(response['subscribedstreamlist']) + '\n')
    assert len(response['streamlist']) > 0
    assert len(response['subscribedstreamlist']) > 0

    print('Testing view all streams returns all streams')
    ViewAllStreamsServiceURL = '/ViewAllStreams'
    ViewAllStreamsJSON = {}
    response = send_request(conn,ViewAllStreamsServiceURL,ViewAllStreamsJSON,True)
    print('Streamlist length is: ' + str(len(response['streamlist'])))
    print('Coverurls length is: ' + str(len(response['coverurls'])))
    assert len(response['streamlist']) > 0
    assert len(response['coverurls']) > 0

    print('Testing unsubscribe to stream')
    UnsubscribeStreamsServiceURL = '/UnsubscribeStreams'
    UnsubscribeStreamsJSON = {"unsubuser": "amy_hindman@yahoo.com","streamname":"amytest"}
    response = send_request(conn,UnsubscribeStreamsServiceURL,UnsubscribeStreamsJSON,True)
    assert response == {'errorcode': 0}
    response = send_request(conn,ManageStreamURL,ManageStreamJSON,True)
    print('Streamlist is: ' + str(response['streamlist']) + '\n')
    print('Subscribed stream list is: ' + str(response['subscribedstreamlist']) + '\n')
    assert len(response['streamlist']) > 0
    assert len(response['subscribedstreamlist']) == 0

    print('Testing get most viewed streams')
    GetMostViewedStreamsURL = '/GetMostViewedStreams'
    GetMostViewedStreamsJSON = {"userid":"amy_hindman@yahoo.com"}
    response = send_request(conn,GetMostViewedStreamsURL,GetMostViewedStreamsJSON,True)
    print ('Most Viewed stream: ' + str(response['mostviewedstreams'][0]))
    assert response['mostviewedstreams'][0]['streamname'] == 'amytest'

    print('Testing deleting created streams.')
    DeleteStreamsServiceURL = '/DeleteStreams'
    DeleteStreamsJSON = {"streamnamestodelete": ["amytest"]}
    response = send_request(conn,DeleteStreamsServiceURL,DeleteStreamsJSON,True)
    assert response == {'errorcode': 0}

    #TODO: This test should fail, but currently passes.  
    print('Testing error case where stream to delete doesnt exist')
    DeleteStreamsServiceURL = '/DeleteStreams'
    DeleteStreamsJSON = {"streamnamestodelete": ["amytest"]}
    response = send_request(conn,DeleteStreamsServiceURL,DeleteStreamsJSON,True)
    assert response == {'errorcode': 0}
