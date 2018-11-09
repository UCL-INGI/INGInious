/**
 *  Copyright (c)  Olivier GOLETTI, 2017 Brandon NAITALI, 2017 Alexandre DUBRAY
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

package src;

import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;

import java.util.List;
import java.util.ArrayList;

public class Runner {

	private static Class [] getClass(String [] args) {
		Class [] c = new Class[args.length];
		for(int i=0;i<args.length;i++){
			try{
				c[i] = Class.forName("src."+args[i]);
			} catch (ClassNotFoundException e) {
				e.printStackTrace();
				System.exit(0);
			}
		}
		return c;
	}

	
	public static void main(String[] args) {
		Result result = JUnitCore.runClasses(getClass(args));
		for (Failure failure: result.getFailures()) {
			System.err.println(failure.getMessage());
		}
        if (result.wasSuccessful() ) {
			System.exit(127);
		}
	}
}
